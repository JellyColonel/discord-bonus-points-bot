"""Discord OAuth2 authentication."""

import requests
from flask import redirect, session, url_for

from web.config import WebConfig


def get_oauth_url():
    """Generate Discord OAuth2 authorization URL."""
    params = {
        "client_id": WebConfig.DISCORD_CLIENT_ID,
        "redirect_uri": WebConfig.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
    }

    url = WebConfig.DISCORD_OAUTH_URL
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{url}?{param_string}"


def exchange_code(code):
    """Exchange authorization code for access token."""
    data = {
        "client_id": WebConfig.DISCORD_CLIENT_ID,
        "client_secret": WebConfig.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": WebConfig.DISCORD_REDIRECT_URI,
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(WebConfig.DISCORD_TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    return response.json()


def get_user_info(access_token):
    """Get user information from Discord."""
    headers = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(WebConfig.DISCORD_USER_URL, headers=headers)
    response.raise_for_status()
    return response.json()


def require_auth(f):
    """Decorator to require authentication for routes."""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function
