"""Flask web application for Bonus Points Dashboard."""

import logging
import time
from typing import Any, Optional

from flask import (
    Flask,
    Response,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf.csrf import CSRFProtect

from flask_session import Session
from web.activities import get_activity_by_id, get_all_activities
from web.auth import exchange_code, get_oauth_url, get_user_info, require_auth
from web.config import WebConfig

# Local imports (no bot dependency)
from web.database import Database, get_today_date
from web.helpers import (
    calculate_bp,
    get_hidden_activity_ids,
    is_event_active,
    prepare_dashboard_data,
    prepare_settings_data,
    rate_limit,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(WebConfig)
Session(app)
csrf = CSRFProtect(app)

# Initialize database
db = Database(str(WebConfig.DB_PATH))
logger.info(f"Web dashboard using database: {WebConfig.DB_PATH}")


@app.teardown_appcontext
def close_db_connection(exception: Optional[BaseException] = None) -> None:
    """Close database connection at the end of each request."""
    db.close_connection()


# ============================================================================
# Request Logging
# ============================================================================


@app.before_request
def before_request_logging() -> None:
    """Store request start time for timing calculation."""
    g.start_time = time.perf_counter()


@app.after_request
def after_request_logging(response: Response) -> Response:
    """Log API requests with timing information."""
    # Only log API routes
    if not request.path.startswith("/api/"):
        return response

    # Calculate request duration
    duration_ms = (time.perf_counter() - g.start_time) * 1000

    # Get user ID if logged in
    user_id = session.get("user", {}).get("id", "anonymous")

    # Build log message
    status_code = response.status_code
    method = request.method
    path = request.path

    # Log format: [API] METHOD /path | User: id | 45ms | status
    log_msg = (
        f"[API] {method} {path} | User: {user_id} | {duration_ms:.0f}ms | {status_code}"
    )

    # Log at appropriate level based on status code
    if status_code >= 500:
        logger.error(log_msg)
    elif status_code >= 400:
        logger.warning(log_msg)
    else:
        logger.info(log_msg)

    return response


# ============================================================================
# API Response Helpers
# ============================================================================


def api_success(**data: Any) -> Response:
    """Return a standardized API success response.

    Example:
        return api_success(balance=100, message="Updated")
        # Returns: {"success": true, "balance": 100, "message": "Updated"}
    """
    return jsonify({"success": True, **data})


def api_error(message: str, status_code: int = 400) -> tuple[Response, int]:
    """Return a standardized API error response.

    Example:
        return api_error("Invalid amount", 400)
        # Returns: {"success": false, "error": "Invalid amount"}, 400
    """
    return jsonify({"success": False, "error": message}), status_code


# ============================================================================
# Input Validation Helpers
# ============================================================================


def validate_activity_id(value: Any) -> tuple[bool, str]:
    """Validate activity_id format.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        return False, "Missing activity_id"
    if not isinstance(value, str):
        return False, "activity_id must be a string"
    # Activity IDs should only contain alphanumeric chars and underscores
    if not all(c.isalnum() or c == "_" for c in value):
        return False, "Invalid activity_id format"
    if len(value) > 50:
        return False, "activity_id too long"
    return True, ""


def validate_boolean(value: Any, field_name: str) -> tuple[bool, bool, str]:
    """Validate and convert a boolean field.

    Returns:
        Tuple of (is_valid, converted_value, error_message)
    """
    if value is None:
        return False, False, f"Missing {field_name}"
    if isinstance(value, bool):
        return True, value, ""
    if isinstance(value, str):
        if value.lower() in ("true", "1", "yes"):
            return True, True, ""
        if value.lower() in ("false", "0", "no"):
            return True, False, ""
    if isinstance(value, int):
        return True, bool(value), ""
    return False, False, f"{field_name} must be a boolean"


def validate_integer(
    value: Any,
    field_name: str,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
) -> tuple[bool, int, str]:
    """Validate and convert an integer field.

    Returns:
        Tuple of (is_valid, converted_value, error_message)
    """
    if value is None:
        return False, 0, f"Missing {field_name}"

    try:
        int_value = int(value)
    except (ValueError, TypeError):
        return False, 0, f"{field_name} must be a number"

    if min_val is not None and int_value < min_val:
        return False, 0, f"{field_name} cannot be less than {min_val}"
    if max_val is not None and int_value > max_val:
        return False, 0, f"{field_name} cannot exceed {max_val}"

    return True, int_value, ""


# ============================================================================
# Authentication Routes
# ============================================================================


@app.route("/")
def index() -> Response:
    """Landing page - redirect to dashboard if logged in, otherwise show login."""
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login")
def login() -> Response | str:
    """Login page with Discord OAuth2."""
    if "user" in session:
        return redirect(url_for("dashboard"))

    oauth_url = get_oauth_url()
    return render_template("login.html", oauth_url=oauth_url)


@app.route("/callback")
def callback() -> Response | tuple[str, int]:
    """OAuth2 callback handler."""
    code = request.args.get("code")

    if not code:
        return "Error: No authorization code provided", 400

    try:
        # Exchange code for token
        token_data = exchange_code(code)
        access_token = token_data.get("access_token")

        # Get user info
        user_info = get_user_info(access_token)

        # Store in session
        # Use global_name (display name) if available, fallback to username
        display_name = user_info.get("global_name") or user_info["username"]

        session["user"] = {
            "id": user_info["id"],
            "username": display_name,  # Store display name as username for simplicity
            "discriminator": user_info.get("discriminator", "0"),
            "avatar": user_info.get("avatar"),
            "access_token": access_token,
        }
        session.permanent = True

        logger.info(f"User {user_info['username']} logged in (ID: {user_info['id']})")
        return redirect(url_for("dashboard"))

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return f"Authentication failed: {str(e)}", 500


@app.route("/logout")
def logout() -> Response:
    """Logout and clear session."""
    if "user" in session:
        logger.info(f"User {session['user']['username']} logged out")
    session.clear()
    return redirect(url_for("login"))


# ============================================================================
# Dashboard Routes
# ============================================================================


@app.route("/dashboard")
@require_auth
def dashboard() -> str:
    """Main dashboard page."""
    user = session["user"]
    user_id = int(user["id"])

    # Get all dashboard data
    data = prepare_dashboard_data(db, user_id)

    return render_template(
        "dashboard.html",
        user=user,
        activities=data["activities"],
        vip_status=data["vip_status"],
        balance=data["balance"],
        total_earned=data["total_earned"],
        total_remaining=data["total_remaining"],
        completed_count=data["completed_count"],
        total_activities=data["total_activities"],
        progress_percentage=data["progress_percentage"],
        event_active=data["event_active"],
    )


@app.route("/settings")
@require_auth
def settings() -> str:
    """Settings page for managing hidden activities."""
    user = session["user"]
    user_id = int(user["id"])

    # Get settings data
    data = prepare_settings_data(db, user_id)

    return render_template(
        "settings.html",
        user=user,
        activities=data["activities"],
        hidden_activities=data["hidden_activities"],
    )


# ============================================================================
# API Routes - Activity Toggle
# ============================================================================


@app.route("/api/toggle_activity", methods=["POST"])
@require_auth
@rate_limit(
    max_requests=60, window_seconds=60
)  # 60 req/min - users may complete many activities
def api_toggle_activity() -> Response | tuple[Response, int]:
    """Toggle activity completion status.

    When completing: stores the BP earned at that moment (with current VIP/event status).
    When uncompleting: uses the stored BP value to subtract (not recalculated).
    """
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    # Validate activity_id
    is_valid, error_msg = validate_activity_id(data.get("activity_id"))
    if not is_valid:
        return api_error(error_msg)
    activity_id = data.get("activity_id")

    # Validate completed (optional, defaults to False)
    completed = data.get("completed", False)
    if not isinstance(completed, bool):
        # Try to coerce to boolean
        is_valid, completed, error_msg = validate_boolean(completed, "completed")
        if not is_valid:
            return api_error(error_msg)

    activity = get_activity_by_id(activity_id)
    if not activity:
        return api_error("Activity not found", 404)

    try:
        today = get_today_date()

        if completed:
            # COMPLETING: Calculate BP at this moment and store it
            vip_status = db.get_user_vip_status(user_id)
            event_active = is_event_active(db, user_id)
            bp = calculate_bp(activity, vip_status, event_active)

            # Store activity with bp_earned
            db.set_activity_status(user_id, activity_id, today, True, bp_earned=bp)

            # Add BP to balance
            new_balance = db.add_user_bp(user_id, bp)
            logger.info(f"User {user_id} completed {activity_id}: +{bp} BP")

            return api_success(
                new_balance=new_balance,
                bp_change=bp,
            )
        else:
            # UNCOMPLETING: Use stored bp_earned value (not recalculated!)
            stored_bp = db.get_activity_bp_earned(user_id, activity_id, today)

            if stored_bp is None:
                # Fallback for old data without bp_earned
                vip_status = db.get_user_vip_status(user_id)
                event_active = is_event_active(db, user_id)
                stored_bp = calculate_bp(activity, vip_status, event_active)
                logger.warning(
                    f"No stored bp_earned for {activity_id}, using calculated: {stored_bp}"
                )

            # Clear activity status
            db.set_activity_status(user_id, activity_id, today, False)

            # Subtract stored BP from balance
            new_balance = db.subtract_user_bp(user_id, stored_bp)
            logger.info(f"User {user_id} uncompleted {activity_id}: -{stored_bp} BP")

            return api_success(
                new_balance=new_balance,
                bp_change=-stored_bp,
            )
    except Exception:
        logger.exception(f"Error toggling activity {activity_id} for user {user_id}")
        return api_error("Failed to update activity", 500)


# ============================================================================
# API Routes - Balance & Status
# ============================================================================


@app.route("/api/set_balance", methods=["POST"])
@require_auth
@rate_limit(max_requests=10, window_seconds=60)  # 10 req/min
def api_set_balance() -> Response | tuple[Response, int]:
    """Set user balance."""
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    # Validate amount
    is_valid, amount, error_msg = validate_integer(
        data.get("amount"), "amount", min_val=0, max_val=1000000
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


@app.route("/api/toggle_vip", methods=["POST"])
@require_auth
@rate_limit(max_requests=10, window_seconds=60)  # 10 req/min
def api_toggle_vip() -> Response | tuple[Response, int]:
    """Toggle VIP status.

    Note: This does NOT recalculate already-completed activities.
    VIP status only affects future completions.
    """
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    # Validate vip_status
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


@app.route("/api/toggle_event", methods=["POST"])
@require_auth
@rate_limit(max_requests=10, window_seconds=60)  # 10 req/min
def api_toggle_event() -> Response | tuple[Response, int]:
    """Toggle x2 BP event status for the current user.

    Note: This does NOT recalculate already-completed activities.
    Event status only affects future completions.
    """
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    # Validate event_status
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
# API Routes - Hidden Activities
# ============================================================================


@app.route("/api/hidden_items", methods=["GET"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def api_hidden_items() -> Response | tuple[Response, int]:
    """Get all hidden activities for the user."""
    user_id = int(session["user"]["id"])

    try:
        hidden_activities = db.get_hidden_activities(user_id)

        return api_success(
            hidden_activities=hidden_activities,
        )
    except Exception:
        logger.exception(f"Error fetching hidden items for user {user_id}")
        return api_error("Failed to fetch hidden items", 500)


@app.route("/api/hide_activity", methods=["POST"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def api_hide_activity() -> Response | tuple[Response, int]:
    """Hide an activity for the user."""
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    # Validate activity_id
    is_valid, error_msg = validate_activity_id(data.get("activity_id"))
    if not is_valid:
        return api_error(error_msg)
    activity_id = data.get("activity_id")

    # Check activity exists
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


@app.route("/api/unhide_activity", methods=["POST"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)
def api_unhide_activity() -> Response | tuple[Response, int]:
    """Unhide an activity for the user."""
    user_id = int(session["user"]["id"])
    data = request.json

    if not data:
        return api_error("Missing request body")

    # Validate activity_id
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
# API Routes - User Data
# ============================================================================


@app.route("/api/user_data", methods=["GET"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)  # 30 req/min - read-only
def api_user_data() -> Response | tuple[Response, int]:
    """Get current user data (for refreshing dashboard)."""
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


@app.route("/api/activity_bp_values", methods=["GET"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)  # 30 req/min - read-only
def api_activity_bp_values() -> Response | tuple[Response, int]:
    """Get all activity BP values with current VIP/event status.

    For completed activities, returns stored bp_earned values.
    For uncompleted activities, returns calculated values based on current status.
    """
    user_id = int(session["user"]["id"])

    try:
        today = get_today_date()
        vip_status = db.get_user_vip_status(user_id)
        event_active = is_event_active(db, user_id)

        # Get completed activities with stored BP
        completed_with_bp = db.get_user_completed_activities_with_bp(user_id, today)
        completed_bp_map = {item[0]: item[1] for item in completed_with_bp}
        completed_ids = set(completed_bp_map.keys())

        # Get hidden activities
        hidden_activity_ids = get_hidden_activity_ids(db, user_id)

        # Calculate BP values for all visible activities
        activity_bp_values = {}
        total_earned = 0
        total_remaining = 0

        for activity in get_all_activities():
            activity_id = activity["id"]

            # Skip hidden activities
            if activity_id in hidden_activity_ids:
                continue

            if activity_id in completed_ids:
                # Use stored BP for completed activities
                stored_bp = completed_bp_map.get(activity_id)
                if stored_bp is not None:
                    bp_value = stored_bp
                else:
                    # Fallback for old data
                    bp_value = calculate_bp(activity, vip_status, event_active)
                total_earned += bp_value
            else:
                # Calculate BP for uncompleted activities
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


@app.route("/api/user_stats", methods=["GET"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)  # 30 req/min - read-only
def api_user_stats() -> Response | tuple[Response, int]:
    """Get user statistics (balance, earned, remaining, progress).

    Only counts visible (non-hidden) activities.
    Uses stored bp_earned for completed activities.
    """
    user_id = int(session["user"]["id"])

    try:
        today = get_today_date()
        vip_status = db.get_user_vip_status(user_id)
        event_active = is_event_active(db, user_id)
        balance = db.get_user_bp_balance(user_id)

        # Get completed activities with stored BP
        completed_with_bp = db.get_user_completed_activities_with_bp(user_id, today)
        completed_bp_map = {item[0]: item[1] for item in completed_with_bp}
        completed_ids = set(completed_bp_map.keys())

        # Get hidden activities
        hidden_activity_ids = get_hidden_activity_ids(db, user_id)

        total_earned = 0
        total_remaining = 0
        visible_total = 0
        visible_completed = 0

        for activity in get_all_activities():
            activity_id = activity["id"]

            # Skip hidden activities
            if activity_id in hidden_activity_ids:
                continue

            visible_total += 1

            if activity_id in completed_ids:
                visible_completed += 1
                # Use stored BP
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


@app.before_request
def refresh_session() -> None:
    session.modified = True


# ============================================================================
# Run Web Server
# ============================================================================


def run_web() -> None:
    """Run the Flask web server."""
    logger.info("=" * 80)
    logger.info("Starting Bonus Points Web Dashboard...")
    logger.info(f"   Host: {WebConfig.HOST}")
    logger.info(f"   Port: {WebConfig.PORT}")
    logger.info(f"   Database: {WebConfig.DB_PATH}")
    logger.info("=" * 80)

    app.run(
        host=WebConfig.HOST,
        port=WebConfig.PORT,
        debug=WebConfig.DEBUG,
        use_reloader=False,
    )


if __name__ == "__main__":
    run_web()
