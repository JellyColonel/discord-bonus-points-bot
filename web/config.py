"""Web dashboard configuration."""

import os
from datetime import timedelta
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
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(
        days=int(os.getenv("SESSION_LIFETIME_DAYS", "30"))
    )
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

    # Database path
    ROOT_DIR = Path(__file__).parent.parent
    DB_PATH = ROOT_DIR / "data" / "bonus_points.db"

    @classmethod
    def validate(cls):
        """Validate required configuration on startup."""
        required = {
            "SECRET_KEY": cls.SECRET_KEY,
            "DISCORD_CLIENT_ID": cls.DISCORD_CLIENT_ID,
            "DISCORD_CLIENT_SECRET": cls.DISCORD_CLIENT_SECRET,
            "DISCORD_REDIRECT_URI": cls.DISCORD_REDIRECT_URI,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file. See .env.example for reference."
            )


# Validate configuration on import
WebConfig.validate()
