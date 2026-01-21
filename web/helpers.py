"""Helper functions for the web dashboard."""

from typing import Any, Dict, List, Set

from web.activities import ACTIVITIES, get_all_activities
from web.database import get_today_date


def is_event_active(db) -> bool:
    """Check if double BP event is currently active.

    Note: This queries the database. If calling multiple times in same request,
    fetch once and reuse the boolean value.

    Args:
        db: Database instance

    Returns:
        True if x2 BP event is active, False otherwise
    """
    event_active = db.get_setting("double_bp_event", "False")
    return event_active == "True"


def calculate_bp(activity: dict, vip_status: bool, event_active: bool) -> int:
    """Calculate BP for an activity considering VIP and event status.

    Args:
        activity: Activity dictionary with 'bp' and 'bp_vip' keys
        vip_status: Boolean indicating if user has VIP
        event_active: Boolean indicating if x2 BP event is active

    Returns:
        Calculated BP amount
    """
    base_bp = activity["bp_vip"] if vip_status else activity["bp"]
    multiplier = 2 if event_active else 1
    return base_bp * multiplier


def prepare_dashboard_data(db, user_id: int) -> Dict[str, Any]:
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
    completed_activities_list = db.get_user_completed_activities(user_id, today)
    completed_activities_set = set(completed_activities_list)
    event_active = is_event_active(db)

    # Prepare activities by category
    activities_by_category = _build_activities_by_category(
        completed_activities_list,
        completed_activities_set,
        vip_status,
        event_active,
    )

    # Calculate totals
    total_earned, total_remaining = _calculate_totals(activities_by_category)

    # Calculate progress
    total_activities = len(get_all_activities())
    completed_count = len(completed_activities_list)
    progress_percentage = (
        int((completed_count / total_activities) * 100) if total_activities > 0 else 0
    )

    return {
        "activities_by_category": activities_by_category,
        "vip_status": vip_status,
        "balance": balance,
        "total_earned": total_earned,
        "total_remaining": total_remaining,
        "completed_count": completed_count,
        "total_activities": total_activities,
        "progress_percentage": progress_percentage,
        "event_active": event_active,
    }


def _build_activities_by_category(
    completed_activities_list: List[str],
    completed_activities_set: Set[str],
    vip_status: bool,
    event_active: bool,
) -> Dict[str, List[Dict[str, Any]]]:
    """Build activities organized by category with completion status.

    Args:
        completed_activities_list: List of completed activity IDs (ordered by completion time)
        completed_activities_set: Set of completed activity IDs (for fast lookup)
        vip_status: Whether user has VIP status
        event_active: Whether x2 BP event is active

    Returns:
        Dictionary mapping category names to lists of activities with status
    """
    # Create lookup dict for all activities by ID
    all_activities_dict = {}
    for category, activities in ACTIVITIES.items():
        for activity in activities:
            all_activities_dict[activity["id"]] = {**activity, "category": category}

    activities_by_category = {}

    for category, activities in ACTIVITIES.items():
        activities_with_status = []

        # First, add completed activities in database order (most recent first)
        for activity_id in completed_activities_list:
            activity = all_activities_dict.get(activity_id)
            if activity and activity["category"] == category:
                bp_value = calculate_bp(activity, vip_status, event_active)
                activities_with_status.append(
                    {**activity, "completed": True, "bp_value": bp_value}
                )

        # Then, add uncompleted activities in config order
        for activity in activities:
            if activity["id"] not in completed_activities_set:
                bp_value = calculate_bp(activity, vip_status, event_active)
                activities_with_status.append(
                    {**activity, "completed": False, "bp_value": bp_value}
                )

        activities_by_category[category] = activities_with_status

    return activities_by_category


def _calculate_totals(
    activities_by_category: Dict[str, List[Dict[str, Any]]],
) -> tuple[int, int]:
    """Calculate total earned and remaining BP from activities.

    Args:
        activities_by_category: Activities organized by category with completion status

    Returns:
        Tuple of (total_earned, total_remaining)
    """
    total_earned = 0
    total_remaining = 0

    for activities in activities_by_category.values():
        for activity in activities:
            if activity["completed"]:
                total_earned += activity["bp_value"]
            else:
                total_remaining += activity["bp_value"]

    return total_earned, total_remaining
