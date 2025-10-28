"""Flask web application for Discord Bonus Points Bot dashboard."""

import logging

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from bot.core.database import Database, get_today_date
from bot.data import ACTIVITIES, get_activity_by_id, get_all_activities
from bot.utils.helpers import calculate_bp, is_event_active
from flask_session import Session
from web.auth import exchange_code, get_oauth_url, get_user_info, require_auth
from web.config import WebConfig

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(WebConfig)
Session(app)

# Initialize database
db = Database(str(WebConfig.DB_PATH))
logger.info(f"Web dashboard using database: {WebConfig.DB_PATH}")

# ============================================================================
# Authentication Routes
# ============================================================================


@app.route("/")
def index():
    """Landing page - redirect to dashboard if logged in, otherwise show login."""
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login")
def login():
    """Login page with Discord OAuth2."""
    if "user" in session:
        return redirect(url_for("dashboard"))

    oauth_url = get_oauth_url()
    return render_template("login.html", oauth_url=oauth_url)


@app.route("/callback")
def callback():
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

        logger.info(f"User {user_info['username']} logged in (ID: {user_info['id']})")
        return redirect(url_for("dashboard"))

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return f"Authentication failed: {str(e)}", 500


@app.route("/logout")
def logout():
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
def dashboard():
    """Main dashboard page."""
    user = session["user"]
    user_id = int(user["id"])
    today = get_today_date()

    # Get user data
    vip_status = db.get_user_vip_status(user_id)
    balance = db.get_user_bp_balance(user_id)
    completed_activities_list = db.get_user_completed_activities(
        user_id, today
    )  # Keep as list to preserve order
    completed_activities_set = set(
        completed_activities_list
    )  # Also keep as set for fast lookup
    event_active = is_event_active(db)

    # Prepare activities by category with completion status
    activities_by_category = {}
    total_earned = 0
    total_remaining = 0

    # Create a lookup dict for all activities by ID
    all_activities_dict = {}
    for category, activities in ACTIVITIES.items():
        for activity in activities:
            all_activities_dict[activity["id"]] = {**activity, "category": category}

    for category, activities in ACTIVITIES.items():
        activities_with_status = []

        # First, add completed activities in database order (most recent first)
        for activity_id in completed_activities_list:
            activity = all_activities_dict.get(activity_id)
            if activity and activity["category"] == category:
                bp_value = calculate_bp(activity, vip_status, db)
                total_earned += bp_value
                activities_with_status.append(
                    {**activity, "completed": True, "bp_value": bp_value}
                )

        # Then, add uncompleted activities in config order
        for activity in activities:
            if activity["id"] not in completed_activities_set:
                bp_value = calculate_bp(activity, vip_status, db)
                total_remaining += bp_value
                activities_with_status.append(
                    {**activity, "completed": False, "bp_value": bp_value}
                )

        activities_by_category[category] = activities_with_status

    # Calculate progress
    total_activities = len(get_all_activities())
    completed_count = len(completed_activities_list)
    progress_percentage = (
        int((completed_count / total_activities) * 100) if total_activities > 0 else 0
    )

    return render_template(
        "dashboard.html",
        user=user,
        activities=activities_by_category,
        vip_status=vip_status,
        balance=balance,
        total_earned=total_earned,
        total_remaining=total_remaining,
        completed_count=completed_count,
        total_activities=total_activities,
        progress_percentage=progress_percentage,
        event_active=event_active,
    )


# ============================================================================
# API Routes
# ============================================================================


@app.route("/api/toggle_activity", methods=["POST"])
@require_auth
def api_toggle_activity():
    """Toggle activity completion status."""
    user_id = int(session["user"]["id"])
    data = request.json

    activity_id = data.get("activity_id")
    completed = data.get("completed", False)

    if not activity_id:
        return jsonify({"error": "Missing activity_id"}), 400

    activity = get_activity_by_id(activity_id)
    if not activity:
        return jsonify({"error": "Activity not found"}), 404

    today = get_today_date()

    # Update activity status
    db.set_activity_status(user_id, activity_id, today, completed)

    # Update balance
    vip_status = db.get_user_vip_status(user_id)
    bp = calculate_bp(activity, vip_status, db)

    if completed:
        new_balance = db.add_user_bp(user_id, bp)
        logger.info(f"User {user_id} completed {activity_id}: +{bp} BP")
    else:
        new_balance = db.subtract_user_bp(user_id, bp)
        logger.info(f"User {user_id} uncompleted {activity_id}: -{bp} BP")

    # TODO: Trigger Discord dashboard update via webhook
    # notify_bot_update(user_id)

    return jsonify(
        {
            "success": True,
            "new_balance": new_balance,
            "bp_change": bp if completed else -bp,
        }
    )


@app.route("/api/set_balance", methods=["POST"])
@require_auth
def api_set_balance():
    """Set user balance."""
    user_id = int(session["user"]["id"])
    data = request.json

    amount = data.get("amount")

    if amount is None:
        return jsonify({"error": "Missing amount"}), 400

    try:
        amount = int(amount)
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400

    if amount < 0:
        return jsonify({"error": "Amount cannot be negative"}), 400

    if amount > 1000000:
        return jsonify({"error": "Amount cannot exceed 1,000,000"}), 400

    db.set_user_bp_balance(user_id, amount)
    logger.info(f"User {user_id} set balance to {amount} BP")

    # TODO: Trigger Discord dashboard update
    # notify_bot_update(user_id)

    return jsonify({"success": True, "new_balance": amount})


@app.route("/api/toggle_vip", methods=["POST"])
@require_auth
def api_toggle_vip():
    """Toggle VIP status."""
    user_id = int(session["user"]["id"])
    data = request.json

    vip_status = data.get("vip_status", False)

    db.set_user_vip_status(user_id, vip_status)
    logger.info(f"User {user_id} set VIP status to {vip_status}")

    # TODO: Trigger Discord dashboard update
    # notify_bot_update(user_id)

    return jsonify({"success": True, "vip_status": vip_status})


@app.route("/api/user_data", methods=["GET"])
@require_auth
def api_user_data():
    """Get current user data (for refreshing dashboard)."""
    user_id = int(session["user"]["id"])
    today = get_today_date()

    vip_status = db.get_user_vip_status(user_id)
    balance = db.get_user_bp_balance(user_id)
    completed_activities = db.get_user_completed_activities(user_id, today)
    event_active = is_event_active(db)

    return jsonify(
        {
            "vip_status": vip_status,
            "balance": balance,
            "completed_activities": completed_activities,
            "event_active": event_active,
        }
    )


@app.route("/api/activity_bp_values", methods=["GET"])
@require_auth
def api_activity_bp_values():
    """Get all activity BP values with current VIP/event status."""
    user_id = int(session["user"]["id"])
    today = get_today_date()

    vip_status = db.get_user_vip_status(user_id)
    completed_activities = set(db.get_user_completed_activities(user_id, today))

    # Calculate BP values for all activities
    activity_bp_values = {}
    total_earned = 0
    total_remaining = 0

    for activity in get_all_activities():
        bp_value = calculate_bp(activity, vip_status, db)
        activity_bp_values[activity["id"]] = bp_value

        if activity["id"] in completed_activities:
            total_earned += bp_value
        else:
            total_remaining += bp_value

    return jsonify(
        {
            "activities": activity_bp_values,
            "total_earned": total_earned,
            "total_remaining": total_remaining,
        }
    )


@app.route("/api/user_stats", methods=["GET"])
@require_auth
def api_user_stats():
    """Get user statistics (balance, earned, remaining, progress)."""
    user_id = int(session["user"]["id"])
    today = get_today_date()

    vip_status = db.get_user_vip_status(user_id)
    balance = db.get_user_bp_balance(user_id)
    completed_activities = set(db.get_user_completed_activities(user_id, today))

    total_earned = 0
    total_remaining = 0

    for activity in get_all_activities():
        bp_value = calculate_bp(activity, vip_status, db)
        if activity["id"] in completed_activities:
            total_earned += bp_value
        else:
            total_remaining += bp_value

    total_activities = len(get_all_activities())
    completed_count = len(completed_activities)

    return jsonify(
        {
            "balance": balance,
            "total_earned": total_earned,
            "total_remaining": total_remaining,
            "completed_count": completed_count,
            "total_activities": total_activities,
        }
    )


# ============================================================================
# Run Web Server
# ============================================================================


def run_web():
    """Run the Flask web server."""
    logger.info("=" * 80)
    logger.info("🚀 Starting Web Dashboard...")
    logger.info(f"   Host: {WebConfig.HOST}")
    logger.info(f"   Port: {WebConfig.PORT}")
    logger.info(f"   Database: {WebConfig.DB_PATH}")
    logger.info("=" * 80)

    app.run(
        host=WebConfig.HOST,
        port=WebConfig.PORT,
        debug=WebConfig.DEBUG,
        use_reloader=False,  # Important when running with bot
    )


if __name__ == "__main__":
    run_web()
