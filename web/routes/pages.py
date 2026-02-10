"""Page routes — HTML-rendering endpoints."""

import logging

from flask import Blueprint, Response, redirect, render_template, request, session, url_for

from web.auth import exchange_code, get_oauth_url, get_user_info, require_auth
from web.helpers import prepare_dashboard_data, prepare_settings_data

logger = logging.getLogger(__name__)

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def index() -> Response:
    """Landing page - redirect to dashboard if logged in, otherwise show login."""
    if "user" in session:
        return redirect(url_for("pages.dashboard"))
    return redirect(url_for("pages.login"))


@pages_bp.route("/login")
def login() -> Response | str:
    """Login page with Discord OAuth2."""
    if "user" in session:
        return redirect(url_for("pages.dashboard"))

    oauth_url = get_oauth_url()
    return render_template("login.html", oauth_url=oauth_url)


@pages_bp.route("/callback")
def callback() -> Response | tuple[str, int]:
    """OAuth2 callback handler."""
    code = request.args.get("code")

    if not code:
        return "Error: No authorization code provided", 400

    try:
        token_data = exchange_code(code)
        access_token = token_data.get("access_token")
        user_info = get_user_info(access_token)

        display_name = user_info.get("global_name") or user_info["username"]

        session["user"] = {
            "id": user_info["id"],
            "username": display_name,
            "discriminator": user_info.get("discriminator", "0"),
            "avatar": user_info.get("avatar"),
        }
        session.permanent = True

        logger.info(f"User {user_info['username']} logged in (ID: {user_info['id']})")
        return redirect(url_for("pages.dashboard"))

    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return redirect(url_for("pages.login"))


@pages_bp.route("/logout")
def logout() -> Response:
    """Logout and clear session."""
    if "user" in session:
        logger.info(f"User {session['user']['username']} logged out")
    session.clear()
    return redirect(url_for("pages.login"))


@pages_bp.route("/dashboard")
@require_auth
def dashboard() -> str:
    """Main dashboard page."""
    from web.app import db

    user = session["user"]
    user_id = int(user["id"])
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


@pages_bp.route("/settings")
@require_auth
def settings() -> str:
    """Settings page for managing hidden activities."""
    from web.app import db

    user = session["user"]
    user_id = int(user["id"])
    data = prepare_settings_data(db, user_id)

    return render_template(
        "settings.html",
        user=user,
        activities=data["activities"],
        hidden_activities=data["hidden_activities"],
        vip_status=data["vip_status"],
        event_active=data["event_active"],
        balance=data["balance"],
    )
