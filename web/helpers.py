"""Helper functions for the web dashboard."""

from __future__ import annotations

import time
from collections import defaultdict
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Tuple

from flask import jsonify, session

from web.activities import get_all_activities
from web.database import get_today_date

if TYPE_CHECKING:
    from web.database import Database


# ============================================================================
# Rate Limiting
# ============================================================================

# In-memory storage for request timestamps: {user_id: [timestamp1, timestamp2, ...]}
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)


def _cleanup_old_requests(user_id: str, window_seconds: int) -> None:
    """Remove timestamps older than the rate limit window.

    Args:
        user_id: User identifier
        window_seconds: Time window in seconds
    """
    if user_id not in _rate_limit_store:
        return
    now = time.time()
    cutoff = now - window_seconds
    _rate_limit_store[user_id] = [
        ts for ts in _rate_limit_store[user_id] if ts > cutoff
    ]
    if not _rate_limit_store[user_id]:
        del _rate_limit_store[user_id]


def _is_rate_limited(user_id: str, max_requests: int, window_seconds: int) -> bool:
    """Check if user has exceeded rate limit.

    Args:
        user_id: User identifier
        max_requests: Maximum requests allowed in window
        window_seconds: Time window in seconds

    Returns:
        True if rate limited, False otherwise
    """
    _cleanup_old_requests(user_id, window_seconds)
    return len(_rate_limit_store[user_id]) >= max_requests


def _record_request(user_id: str) -> None:
    """Record a request timestamp for the user.

    Args:
        user_id: User identifier
    """
    _rate_limit_store[user_id].append(time.time())


def rate_limit(max_requests: int = 30, window_seconds: int = 60) -> Callable:
    """Decorator to rate limit API endpoints.

    Uses in-memory storage with sliding window approach.
    Identifies users by their session user ID.

    Args:
        max_requests: Maximum requests allowed in the time window (default: 30)
        window_seconds: Time window in seconds (default: 60)

    Returns:
        Decorated function that enforces rate limiting

    Example:
        @app.route("/api/action", methods=["POST"])
        @require_auth
        @rate_limit(max_requests=10, window_seconds=60)
        def api_action():
            ...
    """

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get user ID from session (fallback to "anonymous" if not logged in)
            user_id = str(session.get("user", {}).get("id", "anonymous"))

            if _is_rate_limited(user_id, max_requests, window_seconds):
                return jsonify(
                    {
                        "success": False,
                        "error": "Слишком много запросов. Подождите немного.",
                    }
                ), 429

            _record_request(user_id)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_rate_limit_stats() -> Dict[str, int]:
    """Get current rate limit statistics (for debugging).

    Returns:
        Dictionary mapping user IDs to their current request count
    """
    return {
        user_id: len(timestamps) for user_id, timestamps in _rate_limit_store.items()
    }


# ============================================================================
# BP Calculation
# ============================================================================


def is_event_active(db: Database, user_id: int) -> bool:
    """Check if x2 BP event is active for a specific user.

    Args:
        db: Database instance
        user_id: User's Discord ID

    Returns:
        True if x2 BP event is active for this user, False otherwise
    """
    return db.get_user_event_status(user_id)


def calculate_bp(activity: dict, vip_status: bool, event_active: bool) -> int:
    """Calculate BP for an activity considering VIP and event status.

    Args:
        activity: Activity dictionary with 'bp' and 'bp_vip' keys
        vip_status: Boolean indicating if user has VIP
        event_active: Boolean indicating if x2 BP event is active

    Returns:
        Calculated BP amount
    """
    base_bp = activity["bp"]
    vip_multiplier = 2 if vip_status else 1
    event_multiplier = 2 if event_active else 1
    return base_bp * vip_multiplier * event_multiplier


# ============================================================================
# Hidden Activities Logic
# ============================================================================


def get_hidden_activity_ids(
    db: Database,
    user_id: int,
    hidden_activities: Optional[List[str]] = None,
) -> Set[str]:
    """Get the set of activity IDs that should be hidden for a user.

    Args:
        db: Database instance
        user_id: User's Discord ID
        hidden_activities: Pre-fetched hidden activities (optional, will fetch if None)

    Returns:
        Set of activity IDs that should be hidden
    """
    # Fetch if not provided
    if hidden_activities is None:
        hidden_activities = db.get_hidden_activities(user_id)

    return set(hidden_activities)


def is_activity_visible(
    activity: dict,
    hidden_activity_ids: Set[str],
) -> bool:
    """Check if an activity should be visible (not hidden).

    Args:
        activity: Activity dictionary
        hidden_activity_ids: Set of hidden activity IDs

    Returns:
        True if activity should be visible, False if hidden
    """
    return activity["id"] not in hidden_activity_ids


# ============================================================================
# Dashboard Data Preparation
# ============================================================================


def prepare_dashboard_data(db: Database, user_id: int) -> Dict[str, Any]:
    """Prepare all data needed for dashboard rendering.

    Args:
        db: Database instance
        user_id: User's Discord ID

    Returns:
        Dictionary containing all dashboard template variables
    """
    today = get_today_date()

    # Get user data from database
    vip_status = db.get_user_vip_status(user_id)
    balance = db.get_user_bp_balance(user_id)
    event_active = is_event_active(db, user_id)

    # Get completed activities with stored BP values
    completed_with_bp = db.get_user_completed_activities_with_bp(user_id, today)
    completed_activities_list = [item[0] for item in completed_with_bp]

    completed_bp_map = {
        item[0]: item[1] for item in completed_with_bp
    }  # activity_id -> bp_earned
    completed_at_map = {
        item[0]: item[2] for item in completed_with_bp
    }  # activity_id -> completed_at
    completed_activities_set = set(completed_activities_list)

    # Get hidden activities
    hidden_activities = db.get_hidden_activities(user_id)
    hidden_activity_ids = get_hidden_activity_ids(db, user_id, hidden_activities)

    # Get repeatable completions
    repeatable_data = db.get_repeatable_completions(user_id, today)

    # Build activities list with status
    activities_with_status = _build_activities_list(
        completed_activities_list,
        completed_activities_set,
        completed_bp_map,
        completed_at_map,
        hidden_activity_ids,
        vip_status,
        event_active,
        repeatable_data,
    )

    # Calculate totals (only for visible activities)
    total_earned, total_remaining, visible_total, visible_completed = _calculate_totals(
        activities_with_status,
        completed_bp_map,
    )

    # Calculate progress (only visible activities)
    progress_percentage = (
        int((visible_completed / visible_total) * 100) if visible_total > 0 else 0
    )

    return {
        "activities": activities_with_status,
        "vip_status": vip_status,
        "balance": balance,
        "total_earned": total_earned,
        "total_remaining": total_remaining,
        "completed_count": visible_completed,
        "total_activities": visible_total,
        "progress_percentage": progress_percentage,
        "event_active": event_active,
        "hidden_activities": hidden_activities,
    }


def _build_activities_list(
    completed_activities_list: List[str],
    completed_activities_set: Set[str],
    completed_bp_map: Dict[str, Optional[int]],
    completed_at_map: Dict[str, Optional[str]],
    hidden_activity_ids: Set[str],
    vip_status: bool,
    event_active: bool,
    repeatable_data: Optional[Dict[str, List[Tuple[int, str]]]] = None,
) -> List[Dict[str, Any]]:
    """Build flat list of activities with completion status.

    Activities are returned in definition order with hidden activities excluded.

    Args:
        completed_activities_list: List of completed activity IDs (ordered by completion time)
        completed_activities_set: Set of completed activity IDs (for fast lookup)
        completed_bp_map: Map of activity_id -> stored bp_earned
        completed_at_map: Map of activity_id -> completed_at timestamp
        hidden_activity_ids: Set of hidden activity IDs
        vip_status: Whether user has VIP status
        event_active: Whether x2 BP event is active
        repeatable_data: Map of activity_id -> [(bp_earned, completed_at), ...]

    Returns:
        List of activities with status, excluding hidden ones
    """
    if repeatable_data is None:
        repeatable_data = {}

    activities_with_status = []

    for activity in get_all_activities():
        activity_id = activity["id"]

        # Skip hidden activities
        if activity_id in hidden_activity_ids:
            continue

        is_repeatable = activity.get("repeatable", False)

        if is_repeatable:
            # Repeatable activities use separate completions table
            completions = repeatable_data.get(activity_id, [])
            repeat_count = len(completions)
            repeat_total_bp = sum(bp for bp, _ in completions)
            last_completed_at = completions[0][1] if completions else None
            bp_value = calculate_bp(activity, vip_status, event_active)

            activities_with_status.append(
                {
                    **activity,
                    "completed": False,  # Always "active"
                    "repeatable": True,
                    "repeat_count": repeat_count,
                    "repeat_total_bp": repeat_total_bp,
                    "completed_at": last_completed_at,
                    "bp_value": bp_value,
                }
            )
        else:
            is_completed = activity_id in completed_activities_set

            # For completed activities, use stored BP if available
            # For uncompleted, calculate current BP value
            if is_completed:
                stored_bp = completed_bp_map.get(activity_id)
                if stored_bp is not None:
                    bp_value = stored_bp
                else:
                    # Fallback for old data without bp_earned
                    bp_value = calculate_bp(activity, vip_status, event_active)
            else:
                bp_value = calculate_bp(activity, vip_status, event_active)

            activities_with_status.append(
                {
                    **activity,
                    "completed": is_completed,
                    "completed_at": completed_at_map.get(activity_id) if is_completed else None,
                    "bp_value": bp_value,
                }
            )

    return activities_with_status


def _calculate_totals(
    activities_with_status: List[Dict[str, Any]],
    completed_bp_map: Dict[str, Optional[int]],
) -> Tuple[int, int, int, int]:
    """Calculate total earned and remaining BP from visible activities.

    For earned BP, uses stored bp_earned values (not recalculated).
    Repeatable activities add to total_earned but don't count toward progress.

    Args:
        activities_with_status: List of activities with completion status
        completed_bp_map: Map of activity_id -> stored bp_earned

    Returns:
        Tuple of (total_earned, total_remaining, visible_total, visible_completed)
    """
    total_earned = 0
    total_remaining = 0
    visible_total = 0
    visible_completed = 0

    for activity in activities_with_status:
        if activity.get("repeatable"):
            # Repeatable activities contribute to earned BP but not to progress counts
            total_earned += activity.get("repeat_total_bp", 0)
            continue

        visible_total += 1

        if activity["completed"]:
            visible_completed += 1
            # Use the bp_value which is already set correctly in _build_activities_list
            total_earned += activity["bp_value"]
        else:
            total_remaining += activity["bp_value"]

    return total_earned, total_remaining, visible_total, visible_completed


# ============================================================================
# Settings Page Data
# ============================================================================


def prepare_settings_data(db: Database, user_id: int) -> Dict[str, Any]:
    """Prepare data for the settings page.

    Args:
        db: Database instance
        user_id: User's Discord ID

    Returns:
        Dictionary containing settings page data
    """
    hidden_activities = set(db.get_hidden_activities(user_id))
    vip_status = db.get_user_vip_status(user_id)
    event_active = is_event_active(db, user_id)
    balance = db.get_user_bp_balance(user_id)

    # Build activities list with hidden status and calculated BP
    all_activities = []
    for activity in get_all_activities():
        bp_value = calculate_bp(activity, vip_status, event_active)
        all_activities.append(
            {
                **activity,
                "hidden": activity["id"] in hidden_activities,
                "bp_value": bp_value,
            }
        )

    return {
        "activities": all_activities,
        "hidden_activities": list(hidden_activities),
        "vip_status": vip_status,
        "event_active": event_active,
        "balance": balance,
    }
