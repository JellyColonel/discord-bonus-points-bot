# bonus_points_bot/bot/core/bot.py
"""Bot class and setup."""

import logging
from datetime import datetime, time, timedelta

import discord
import pytz
from discord.ext import tasks

from bot.commands import setup_all_commands
from bot.core.database import Database

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
        logger.info("BonusPointsBot instance created")

    async def setup_hook(self):
        """Setup hook called when bot starts."""
        # Only setup commands here, don't sync yet
        if not self.synced:
            logger.info("🔧 Setting up commands...")
            setup_all_commands(self.tree, self.db, self.config)
            logger.info("✅ Commands setup complete")

    async def on_ready(self):
        """Called when bot is ready and connected."""
        logger.info("=" * 80)
        logger.info(f"✅ Bot logged in as: {self.user} (ID: {self.user.id})")
        logger.info(f"📡 Connected to {len(self.guilds)} server(s)")
        logger.info("=" * 80)

        # Log which guilds the bot is in
        for guild in self.guilds:
            logger.info(
                f"   📍 Guild: {guild.name} (ID: {guild.id}, Members: {guild.member_count})"
            )

        # Now sync commands (guilds are available now!)
        if not self.synced:
            if self.config.GUILD_ID and self.config.GUILD_ID.isdigit():
                guild = discord.Object(id=int(self.config.GUILD_ID))

                logger.info(f"🔄 Syncing commands to guild {self.config.GUILD_ID}...")
                try:
                    # CRITICAL: Copy global commands to guild first!
                    self.tree.copy_global_to(guild=guild)
                    logger.debug("Commands copied to guild")

                    # Now sync
                    synced = await self.tree.sync(guild=guild)
                    logger.info(
                        f"✅ Successfully synced {len(synced)} commands to guild {self.config.GUILD_ID}"
                    )
                    for cmd in synced:
                        logger.debug(f"   - /{cmd.name}: {cmd.description}")
                except discord.HTTPException as e:
                    logger.error(f"❌ Failed to sync commands to guild: {e}")
                    logger.error(f"Error details: {e.text}")
            else:
                # Sync globally
                logger.info("🌍 Syncing commands globally...")
                logger.warning(
                    "⚠️  GUILD_ID not set or invalid - global sync takes up to 1 hour!"
                )
                try:
                    synced = await self.tree.sync()
                    logger.info(
                        f"✅ Successfully synced {len(synced)} commands globally"
                    )
                    for cmd in synced:
                        logger.debug(f"   - /{cmd.name}: {cmd.description}")
                except discord.HTTPException as e:
                    logger.error(f"❌ Failed to sync commands globally: {e}")

            self.synced = True

        # Start daily reset task
        logger.info("⏰ Scheduling daily reset task for 07:00 Moscow Time")
        if not self.daily_reset.is_running():
            self.daily_reset.start()
            logger.info("✅ Daily reset task started")

        logger.info("=" * 80)
        logger.info("🎉 Bot is ready and listening for commands!")
        logger.info("=" * 80)

    async def on_disconnect(self):
        """Called when bot disconnects."""
        logger.warning("⚠️  Bot disconnected from Discord")

    async def on_resumed(self):
        """Called when bot resumes connection."""
        logger.info("🔌 Bot connection resumed")

    async def on_guild_join(self, guild):
        """Called when bot joins a new guild."""
        logger.info(
            f"➕ Bot joined new guild: {guild.name} (ID: {guild.id}, Members: {guild.member_count})"
        )

    async def on_guild_remove(self, guild):
        """Called when bot leaves a guild."""
        logger.info(f"➖ Bot removed from guild: {guild.name} (ID: {guild.id})")

    async def on_command_error(self, interaction, error):
        """Called when a command encounters an error."""
        logger.error(
            f"❌ Command error in {interaction.command.name if hasattr(interaction, 'command') else 'unknown'}: {error}",
            exc_info=True,
        )

    @tasks.loop(time=time(hour=7, minute=0, tzinfo=pytz.timezone("Europe/Moscow")))
    async def daily_reset(self):
        """Daily reset task - resets all activities to incomplete."""
        logger.info("=" * 80)
        logger.info("🔄 DAILY RESET STARTING")
        logger.info("=" * 80)

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            # Get today's date
            today = datetime.now(pytz.timezone("Europe/Moscow")).strftime("%Y-%m-%d")
            logger.info(f"Reset date: {today}")

            # Set all today's activities to incomplete (0)
            cursor.execute(
                """
                UPDATE activities 
                SET completed = 0 
                WHERE date = ?
            """,
                (today,),
            )

            reset_count = cursor.rowcount
            logger.info(f"✅ Reset {reset_count} activity records to incomplete")

            # Optional: Delete old records (keep last 30 days for history)
            cutoff_date = (
                datetime.now(pytz.timezone("Europe/Moscow")) - timedelta(days=30)
            ).strftime("%Y-%m-%d")
            cursor.execute("DELETE FROM activities WHERE date < ?", (cutoff_date,))

            deleted = cursor.rowcount
            if deleted > 0:
                logger.info(
                    f"🗑️  Deleted {deleted} old activity records (before {cutoff_date})"
                )

            conn.commit()
            conn.close()

            logger.info("=" * 80)
            logger.info("✅ DAILY RESET COMPLETE")
            logger.info("=" * 80)
        except Exception as e:
            logger.error("=" * 80)
            logger.error(f"❌ DAILY RESET FAILED: {e}", exc_info=True)
            logger.error("=" * 80)

    @daily_reset.before_loop
    async def before_daily_reset(self):
        """Wait for bot to be ready before starting the reset loop."""
        await self.wait_until_ready()
        logger.info("⏰ Daily reset task ready to run at 07:00 Moscow Time")
