"""API routes — JSON endpoints."""

import logging
from datetime import datetime, timezone

from flask import Blueprint, Response, request, session

from web.activities import get_activity_by_id, get_all_activities, is_repeatable
from web.auth import require_auth
from web.database import get_today_date
from web.helpers import (
    calculate_bp,
    get_hidden_activity_ids,
    is_activity_visible,
    is_event_active,
    rate_limit,
)
from web.validation import (
    MAX_BALANCE,
    api_error,
    api_success,
    validate_activity_id,
    validate_boolean,
    validate_integer,
)

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


def _get_db():
    from web.app import db
    return db


# ============================================================================
# Activity Toggle
# ============================================================================


@api_bp.route("/toggle_activity", methods=["POST"])
@require_auth
@rate_limit(max_requests=60, window_seconds=60)
def toggle_activity() -> Response | tuple[Response, int]:
    """Toggle activity completion status."""
    db = _get_db()
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    is_valid, error_msg = validate_activity_id(data.get("activity_id"))
    if not is_valid:
        return api_error(error_msg)
    activity_id = data.get("activity_id")

    completed = data.get("completed", False)
    if not isinstance(completed, bool):
        is_valid, completed, error_msg = validate_boolean(completed, "completed")
        if not is_valid:
            return api_error(error_msg)

    activity = get_activity_by_id(activity_id)
    if not activity:
        return api_error("Activity not found", 404)

    hidden_ids = get_hidden_activity_ids(db, user_id)
    if not is_activity_visible(activity, hidden_ids):
        return api_error("Activity is hidden")

    try:
        today = get_today_date()

        if completed:
            vip_status = db.get_user_vip_status(user_id)
            event_active = is_event_active(db, user_id)
            bp = calculate_bp(activity, vip_status, event_active)

            db.set_activity_status(user_id, activity_id, today, True, bp_earned=bp)
            new_balance = db.add_user_bp(user_id, bp)
            logger.info(f"User {user_id} completed {activity_id}: +{bp} BP")

            return api_success(
                new_balance=new_balance,
                bp_change=bp,
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
        else:
            stored_bp = db.get_activity_bp_earned(user_id, activity_id, today)

            if stored_bp is None:
                vip_status = db.get_user_vip_status(user_id)
                event_active = is_event_active(db, user_id)
                stored_bp = calculate_bp(activity, vip_status, event_active)
                logger.warning(
                    f"No stored bp_earned for {activity_id}, using calculated: {stored_bp}"
                )

            db.set_activity_status(user_id, activity_id, today, False)
            new_balance = db.subtract_user_bp(user_id, stored_bp)
            logger.info(f"User {user_id} uncompleted {activity_id}: -{stored_bp} BP")

            return api_success(new_balance=new_balance, bp_change=-stored_bp)
    except Exception:
        logger.exception(f"Error toggling activity {activity_id} for user {user_id}")
        return api_error("Failed to update activity", 500)


# ============================================================================
# Repeatable Activities
# ============================================================================


@api_bp.route("/repeatable_activity", methods=["POST"])
@require_auth
@rate_limit(max_requests=60, window_seconds=60)
def repeatable_activity() -> Response | tuple[Response, int]:
    """Add or remove a repeatable activity completion."""
    db = _get_db()
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    is_valid, error_msg = validate_activity_id(data.get("activity_id"))
    if not is_valid:
        return api_error(error_msg)
    activity_id = data.get("activity_id")

    action = data.get("action")
    if action not in ("add", "remove"):
        return api_error("action must be 'add' or 'remove'")

    activity = get_activity_by_id(activity_id)
    if not activity:
        return api_error("Activity not found", 404)

    if not is_repeatable(activity_id):
        return api_error("Activity is not repeatable")

    hidden_ids = get_hidden_activity_ids(db, user_id)
    if not is_activity_visible(activity, hidden_ids):
        return api_error("Activity is hidden")

    try:
        today = get_today_date()

        if action == "add":
            max_completions = activity.get("max_completions")
            if max_completions is not None:
                current = db.get_repeatable_completions(user_id, today)
                current_count = len(current.get(activity_id, []))
                if current_count >= max_completions:
                    return api_error(
                        f"Достигнут лимит выполнений ({max_completions}) на сегодня"
                    )

            vip_status = db.get_user_vip_status(user_id)
            event_active = is_event_active(db, user_id)
            bp = calculate_bp(activity, vip_status, event_active)

            count = db.add_repeatable_completion(user_id, activity_id, today, bp)
            new_balance = db.add_user_bp(user_id, bp)

            # Calculate total BP for this repeatable activity today
            completions = db.get_repeatable_completions(user_id, today)
            activity_completions = completions.get(activity_id, [])
            total_bp = sum(bp_earned for bp_earned, _ in activity_completions)

            logger.info(f"User {user_id} added repeatable {activity_id}: +{bp} BP (count={count})")

            return api_success(
                new_balance=new_balance,
                bp_change=bp,
                count=count,
                total_bp=total_bp,
                max_completions=activity.get("max_completions"),
                completed_at=datetime.now(timezone.utc).isoformat(),
            )
        else:
            count, removed_bp = db.remove_repeatable_completion(user_id, activity_id, today)

            if removed_bp == 0:
                return api_error("No completions to remove")

            new_balance = db.subtract_user_bp(user_id, removed_bp)

            # Calculate total BP for this repeatable activity today
            completions = db.get_repeatable_completions(user_id, today)
            activity_completions = completions.get(activity_id, [])
            total_bp = sum(bp_earned for bp_earned, _ in activity_completions)
            last_completed_at = activity_completions[0][1] if activity_completions else None

            logger.info(
                f"User {user_id} removed repeatable {activity_id}: "
                f"-{removed_bp} BP (count={count})"
            )

            return api_success(
                new_balance=new_balance,
                bp_change=-removed_bp,
                count=count,
                total_bp=total_bp,
                max_completions=activity.get("max_completions"),
                completed_at=last_completed_at,
            )
    except Exception:
        logger.exception(f"Error with repeatable activity {activity_id} for user {user_id}")
        return api_error("Failed to update activity", 500)


# ============================================================================
# Balance & Status
# ============================================================================


@api_bp.route("/set_balance", methods=["POST"])
@require_auth
@rate_limit(max_requests=10, window_seconds=60)
def set_balance() -> Response | tuple[Response, int]:
    """Set user balance."""
    db = _get_db()
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    is_valid, amount, error_msg = validate_integer(
        data.get("amount"), "amount", min_val=0, max_val=MAX_BALANCE
    )
    if not is_valid:
        return api_error(error_msg)

    try:
        db.set_user_bp_balance(user_id, amount)
        logger.info(f"User {user_id} set balance to {amount} BP")
        return api_success(new_balance=amount)
    except Exception:
        logger.exception(f"Error setting balance for user {user_id}")
        return api_error("Failed to update balance", 500)


@api_bp.route("/toggle_vip", methods=["POST"])
@require_auth
@rate_limit(max_requests=10, window_seconds=60)
def toggle_vip() -> Response | tuple[Response, int]:
    """Toggle VIP status."""
    db = _get_db()
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    is_valid, vip_status, error_msg = validate_boolean(
        data.get("vip_status"), "vip_status"
    )
    if not is_valid:
        return api_error(error_msg)

    try:
        db.set_user_vip_status(user_id, vip_status)
        logger.info(f"User {user_id} set VIP status to {vip_status}")
        return api_success(vip_status=vip_status)
    except Exception:
        logger.exception(f"Error toggling VIP for user {user_id}")
        return api_error("Failed to update VIP status", 500)


@api_bp.route("/toggle_event", methods=["POST"])
@require_auth
@rate_limit(max_requests=10, window_seconds=60)
def toggle_event() -> Response | tuple[Response, int]:
    """Toggle x2 BP event status for the current user."""
    db = _get_db()
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    is_valid, event_status, error_msg = validate_boolean(
        data.get("event_status"), "event_status"
    )
    if not is_valid:
        return api_error(error_msg)

    try:
        db.set_user_event_status(user_id, event_status)
        logger.info(f"User {user_id} set event status to {event_status}")
        return api_success(event_status=event_status)
    except Exception:
        logger.exception(f"Error toggling event status for user {user_id}")
        return api_error("Failed to update event status", 500)


# ============================================================================
# Hidden Activities
# ============================================================================


@api_bp.route("/hidden_items", methods=["GET"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def hidden_items() -> Response | tuple[Response, int]:
    """Get all hidden activities for the user."""
    db = _get_db()
    user_id = int(session["user"]["id"])

    try:
        hidden_activities = db.get_hidden_activities(user_id)
        return api_success(hidden_activities=hidden_activities)
    except Exception:
        logger.exception(f"Error fetching hidden items for user {user_id}")
        return api_error("Failed to fetch hidden items", 500)


@api_bp.route("/hide_activity", methods=["POST"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def hide_activity() -> Response | tuple[Response, int]:
    """Hide an activity for the user."""
    db = _get_db()
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    is_valid, error_msg = validate_activity_id(data.get("activity_id"))
    if not is_valid:
        return api_error(error_msg)
    activity_id = data.get("activity_id")

    if not get_activity_by_id(activity_id):
        return api_error("Activity not found", 404)

    try:
        was_hidden = db.hide_activity(user_id, activity_id)
        logger.info(f"User {user_id} hid activity {activity_id}")
        return api_success(
            activity_id=activity_id,
            hidden=True,
            was_already_hidden=not was_hidden,
        )
    except Exception:
        logger.exception(f"Error hiding activity {activity_id} for user {user_id}")
        return api_error("Failed to hide activity", 500)


@api_bp.route("/unhide_activity", methods=["POST"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def unhide_activity() -> Response | tuple[Response, int]:
    """Unhide an activity for the user."""
    db = _get_db()
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    is_valid, error_msg = validate_activity_id(data.get("activity_id"))
    if not is_valid:
        return api_error(error_msg)
    activity_id = data.get("activity_id")

    try:
        was_unhidden = db.unhide_activity(user_id, activity_id)
        logger.info(f"User {user_id} unhid activity {activity_id}")
        return api_success(
            activity_id=activity_id,
            hidden=False,
            was_already_visible=not was_unhidden,
        )
    except Exception:
        logger.exception(f"Error unhiding activity {activity_id} for user {user_id}")
        return api_error("Failed to unhide activity", 500)


# ============================================================================
# User Data
# ============================================================================


@api_bp.route("/user_data", methods=["GET"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def user_data() -> Response | tuple[Response, int]:
    """Get current user data (for refreshing dashboard)."""
    db = _get_db()
    user_id = int(session["user"]["id"])

    try:
        today = get_today_date()
        vip_status = db.get_user_vip_status(user_id)
        balance = db.get_user_bp_balance(user_id)
        completed_activities = db.get_user_completed_activities(user_id, today)
        event_active = is_event_active(db, user_id)
        hidden_activities = db.get_hidden_activities(user_id)

        return api_success(
            vip_status=vip_status,
            balance=balance,
            completed_activities=completed_activities,
            event_active=event_active,
            hidden_activities=hidden_activities,
        )
    except Exception:
        logger.exception(f"Error fetching user data for user {user_id}")
        return api_error("Failed to fetch user data", 500)


@api_bp.route("/activity_bp_values", methods=["GET"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def activity_bp_values() -> Response | tuple[Response, int]:
    """Get all activity BP values with current VIP/event status."""
    db = _get_db()
    user_id = int(session["user"]["id"])

    try:
        today = get_today_date()
        vip_status = db.get_user_vip_status(user_id)
        event_active = is_event_active(db, user_id)

        completed_with_bp = db.get_user_completed_activities_with_bp(user_id, today)
        completed_bp_map = {item[0]: item[1] for item in completed_with_bp}
        completed_ids = set(completed_bp_map.keys())

        hidden_activity_ids = get_hidden_activity_ids(db, user_id)

        activity_bp_values = {}
        total_earned = 0
        total_remaining = 0

        for activity in get_all_activities():
            activity_id = activity["id"]

            if activity_id in hidden_activity_ids:
                continue

            if activity_id in completed_ids:
                stored_bp = completed_bp_map.get(activity_id)
                if stored_bp is not None:
                    bp_value = stored_bp
                else:
                    bp_value = calculate_bp(activity, vip_status, event_active)
                total_earned += bp_value
            else:
                bp_value = calculate_bp(activity, vip_status, event_active)
                total_remaining += bp_value

            activity_bp_values[activity_id] = bp_value

        return api_success(
            activities=activity_bp_values,
            total_earned=total_earned,
            total_remaining=total_remaining,
        )
    except Exception:
        logger.exception(f"Error fetching activity BP values for user {user_id}")
        return api_error("Failed to fetch activity values", 500)


@api_bp.route("/user_stats", methods=["GET"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def user_stats() -> Response | tuple[Response, int]:
    """Get user statistics (balance, earned, remaining, progress)."""
    db = _get_db()
    user_id = int(session["user"]["id"])

    try:
        today = get_today_date()
        vip_status = db.get_user_vip_status(user_id)
        event_active = is_event_active(db, user_id)
        balance = db.get_user_bp_balance(user_id)

        completed_with_bp = db.get_user_completed_activities_with_bp(user_id, today)
        completed_bp_map = {item[0]: item[1] for item in completed_with_bp}
        completed_ids = set(completed_bp_map.keys())

        hidden_activity_ids = get_hidden_activity_ids(db, user_id)

        # Get repeatable completions
        repeatable_data = db.get_repeatable_completions(user_id, today)

        total_earned = 0
        total_remaining = 0
        visible_total = 0
        visible_completed = 0

        for activity in get_all_activities():
            activity_id = activity["id"]

            if activity_id in hidden_activity_ids:
                continue

            if activity.get("repeatable"):
                # Repeatable: add earned BP but don't count toward progress
                completions = repeatable_data.get(activity_id, [])
                total_earned += sum(bp for bp, _ in completions)
                continue

            visible_total += 1

            if activity_id in completed_ids:
                visible_completed += 1
                stored_bp = completed_bp_map.get(activity_id)
                if stored_bp is not None:
                    total_earned += stored_bp
                else:
                    total_earned += calculate_bp(activity, vip_status, event_active)
            else:
                total_remaining += calculate_bp(activity, vip_status, event_active)

        return api_success(
            balance=balance,
            total_earned=total_earned,
            total_remaining=total_remaining,
            completed_count=visible_completed,
            total_activities=visible_total,
        )
    except Exception:
        logger.exception(f"Error fetching user stats for user {user_id}")
        return api_error("Failed to fetch user stats", 500)


# ============================================================================
# Onboarding
# ============================================================================


@api_bp.route("/complete_onboarding", methods=["POST"])
@require_auth
@rate_limit(max_requests=10, window_seconds=60)
def complete_onboarding() -> Response | tuple[Response, int]:
    """Create a user row with defaults (used when skipping onboarding)."""
    db = _get_db()
    user_id = int(session["user"]["id"])

    try:
        db.ensure_user_exists(user_id)
        logger.info(f"User {user_id} completed onboarding (skip)")
        return api_success()
    except Exception:
        logger.exception(f"Error completing onboarding for user {user_id}")
        return api_error("Failed to complete onboarding", 500)


# ============================================================================
# Reset Activities
# ============================================================================


@api_bp.route("/reset_today_activities", methods=["POST"])
@require_auth
@rate_limit(max_requests=5, window_seconds=60)
def reset_today_activities() -> Response | tuple[Response, int]:
    """Reset all of today's activity completions without changing BP balance."""
    db = _get_db()
    user_id = int(session["user"]["id"])

    try:
        today = get_today_date()
        regular_deleted, repeatable_deleted = db.reset_today_activities(user_id, today)
        total_deleted = regular_deleted + repeatable_deleted
        balance = db.get_user_bp_balance(user_id)

        logger.info(
            f"User {user_id} reset today's activities: "
            f"{regular_deleted} regular, {repeatable_deleted} repeatable"
        )

        return api_success(
            deleted_count=total_deleted,
            balance=balance,
        )
    except Exception:
        logger.exception(f"Error resetting activities for user {user_id}")
        return api_error("Failed to reset activities", 500)
