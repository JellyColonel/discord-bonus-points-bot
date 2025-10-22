"""Configuration module."""

import os
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Bot configuration."""
    
    def __init__(self):
        # Load environment variables from .env file
        env_path = Path(__file__).parent.parent.parent / ".env"
        load_dotenv(env_path)
        
        # Discord configuration
        self.TOKEN = os.getenv("DISCORD_TOKEN")
        self.GUILD_ID = os.getenv("GUILD_ID")  # Optional: for faster command sync
        
        # Admin settings
        self.ADMIN_ROLE_ID = os.getenv("ADMIN_ROLE_ID")  # Discord role ID for admins
        
        # Event settings
        self.DOUBLE_BP_EVENT = os.getenv("DOUBLE_BP_EVENT", "False") == "True"
        
        # Paths
        self.ROOT_DIR = Path(__file__).parent.parent.parent
        self.DATA_DIR = self.ROOT_DIR / "data"
        self.LOGS_DIR = self.ROOT_DIR / "logs"
        
    def __repr__(self):
        return f"<Config guild_id={self.GUILD_ID} event={self.DOUBLE_BP_EVENT}>"
