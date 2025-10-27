"""Web dashboard configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class WebConfig:
    """Web dashboard configuration."""

    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True

    # Discord OAuth2
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
    DISCORD_API_BASE = "https://discord.com/api/v10"
    DISCORD_OAUTH_URL = f"{DISCORD_API_BASE}/oauth2/authorize"
    DISCORD_TOKEN_URL = f"{DISCORD_API_BASE}/oauth2/token"
    DISCORD_USER_URL = f"{DISCORD_API_BASE}/users/@me"

    # Web server settings
    HOST = os.getenv("WEB_HOST", "0.0.0.0")
    PORT = int(os.getenv("WEB_PORT", 5000))
    DEBUG = os.getenv("WEB_DEBUG", "False") == "True"

    # Database path (shared with bot)
    ROOT_DIR = Path(__file__).parent.parent
    DB_PATH = ROOT_DIR / "data" / "bonus_points.db"
