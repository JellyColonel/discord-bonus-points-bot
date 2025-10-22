"""Bot class and setup."""

import logging
from datetime import time

import discord
import pytz
from discord.ext import tasks

from commands import setup_all_commands
from core.database import Database

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
            if self.config.GUILD_ID and self.config.GUILD_ID.isdigit():
                guild = discord.Object(id=int(self.config.GUILD_ID))

                # Setup commands
                logger.info("🔎 Setting up commands...")
                setup_all_commands(self.tree, self.db, self.config)

                # Sync to guild
                logger.info(f"🔄 Syncing commands to guild {self.config.GUILD_ID}...")
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)

                logger.info(f"✅ Commands synced to guild {self.config.GUILD_ID}")
            else:
                # Setup commands
                setup_all_commands(self.tree, self.db, self.config)

                # No guild specified, sync globally
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
                logger.info(
                    "✅ Commands synced globally (this may take up to 1 hour to propagate)"
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
