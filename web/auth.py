"""Discord OAuth2 authentication."""

from functools import wraps
from typing import Any, Callable, Dict, TypeVar

import requests
from flask import Response, redirect, session, url_for

from web.config import WebConfig

# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])


def get_oauth_url() -> str:
    """Generate Discord OAuth2 authorization URL."""
    params: Dict[str, Any] = {
        "client_id": WebConfig.DISCORD_CLIENT_ID,
        "redirect_uri": WebConfig.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify guilds",
    }

    url = WebConfig.DISCORD_OAUTH_URL
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{url}?{param_string}"


def exchange_code(code: str) -> Dict[str, Any]:
    """Exchange authorization code for access token."""
    data: Dict[str, Any] = {
        "client_id": WebConfig.DISCORD_CLIENT_ID,
        "client_secret": WebConfig.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": WebConfig.DISCORD_REDIRECT_URI,
    }

    headers: Dict[str, str] = {"Content-Type": "application/x-www-form-urlencoded"}

    response = requests.post(WebConfig.DISCORD_TOKEN_URL, data=data, headers=headers)
    response.raise_for_status()
    return response.json()


def get_user_info(access_token: str) -> Dict[str, Any]:
    """Get user information from Discord."""
    headers: Dict[str, str] = {"Authorization": f"Bearer {access_token}"}

    response = requests.get(WebConfig.DISCORD_USER_URL, headers=headers)
    response.raise_for_status()
    return response.json()


def require_auth(f: F) -> F:
    """Decorator to require authentication for routes."""

    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Response:
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function  # type: ignore[return-value]
