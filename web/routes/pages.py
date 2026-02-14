"""Page routes — HTML-rendering endpoints."""

import logging

from flask import Blueprint, Response, redirect, render_template, request, session, url_for

from web.auth import exchange_code, get_oauth_url, get_user_info, require_auth, verify_oauth_state
from web.helpers import (
    is_returning_user,
    prepare_dashboard_data,
    prepare_recipes_data,
    prepare_settings_data,
)
from web.validation import MAX_BALANCE

logger = logging.getLogger(__name__)

pages_bp = Blueprint("pages", __name__)


def _get_db():
    from web.app import db

    return db


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
    state = request.args.get("state")

    if not code:
        logger.warning("OAuth callback: no authorization code provided")
        return redirect(url_for("pages.login"))

    if not verify_oauth_state(state):
        logger.warning("OAuth callback: state mismatch (possible CSRF)")
        return redirect(url_for("pages.login"))

    try:
        token_data = exchange_code(code)
        access_token = token_data.get("access_token")

        if not access_token:
            logger.error("OAuth callback: no access_token in token response")
            return redirect(url_for("pages.login"))

        user_info = get_user_info(access_token)

        display_name = user_info.get("global_name") or user_info["username"]

        session["user"] = {
            "id": user_info["id"],
            "username": display_name,
            "discriminator": user_info.get("discriminator", "0"),
            "avatar": user_info.get("avatar"),
        }
        session.permanent = True

        # Check returning user BEFORE updating timestamp (order matters)
        db = _get_db()
        user_id = int(user_info["id"])
        if db.user_exists(user_id):
            session["show_returning_reminder"] = is_returning_user(db, user_id)
            db.update_last_login(user_id)
        else:
            session["show_returning_reminder"] = False

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
    db = _get_db()
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
        is_new_user=data["is_new_user"],
        is_returning_user=data["is_returning_user"],
        max_balance=MAX_BALANCE,
    )


@pages_bp.route("/settings")
@require_auth
def settings() -> str:
    """Settings page for managing hidden activities."""
    db = _get_db()
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
        max_balance=MAX_BALANCE,
    )


@pages_bp.route("/recipes")
@require_auth
def recipes() -> str:
    """Recipes page with ingredient trees and shopping lists."""
    user = session["user"]
    data = prepare_recipes_data()

    return render_template(
        "recipes.html",
        user=user,
        recipes_data=data,
    )
