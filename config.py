import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # Optional: for faster command sync

# Admin settings
ADMIN_ROLE_ID = os.getenv(
    "ADMIN_ROLE_ID"
)  # Discord role ID for admins who can toggle events

# Event settings
DOUBLE_BP_EVENT = (
    os.getenv("DOUBLE_BP_EVENT", "False") == "True"
)  # Set to True during server events to double all BP earnings
