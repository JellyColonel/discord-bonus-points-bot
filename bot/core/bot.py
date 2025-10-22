"""Bot class and setup."""

import logging
from datetime import time

import discord
import pytz
from discord.ext import tasks

from bot.commands import setup_all_commands  # FIXED: Added 'bot.' prefix
from bot.core.database import Database  # FIXED: Full path

logger = logging.getLogger(__name__)


class BonusPointsBot(discord.Client):
    """Main bot class."""

    def __init__(self, db: Database, config):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.db = db
        self.config = config
        self.synced = False  # Flag to prevent multiple syncs

    async def setup_hook(self):
        """Setup hook called when bot is ready."""
        # Only sync commands if not already synced
        if not self.synced:
            # Setup commands first
            logger.info("🔎 Setting up commands...")
            setup_all_commands(self.tree, self.db, self.config)

            if self.config.GUILD_ID and self.config.GUILD_ID.isdigit():
                guild = discord.Object(id=int(self.config.GUILD_ID))

                # Sync to specific guild (faster, for testing)
                logger.info(f"🔄 Syncing commands to guild {self.config.GUILD_ID}...")
                await self.tree.sync(guild=guild)
                logger.info(f"✅ Commands synced to guild {self.config.GUILD_ID}")
            else:
                # Sync globally (slower, takes up to 1 hour)
                logger.info("🔄 Syncing commands globally...")
                await self.tree.sync()
                logger.info(
                    "✅ Commands synced globally (may take up to 1 hour to propagate)"
                )

            self.synced = True

    async def on_ready(self):
        """Called when bot is ready."""
        logger.info(f"✅ Logged in as {self.user}")
        logger.info(f"📡 Connected to {len(self.guilds)} server(s)")
        logger.info("⏰ Daily reset scheduled for 07:00 Moscow Time")

        if not self.daily_reset.is_running():
            self.daily_reset.start()

        logger.info("🎉 Bot is ready to use!")

    @tasks.loop(time=time(hour=7, minute=0, tzinfo=pytz.timezone("Europe/Moscow")))
    async def daily_reset(self):
        """Daily reset task."""
        logger.info("🔄 Daily reset executed")
