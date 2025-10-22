import logging
from datetime import time

import discord
import pytz
from discord.ext import tasks

import config
from commands import setup_commands
from database import Database

# Setup discord.py's logging manually
discord.utils.setup_logging(level=logging.INFO, root=True)

# Reduce HTTP spam
logging.getLogger("discord.http").setLevel(logging.WARNING)

# Get logger for our bot
logger = logging.getLogger(__name__)


class BonusPointsBot(discord.Client):
    def __init__(self, db):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.tree = discord.app_commands.CommandTree(self)
        self.db = db
        self.synced = False  # Flag to prevent multiple syncs

    async def setup_hook(self):
        # Only sync commands if not already synced
        if not self.synced:
            if config.GUILD_ID and config.GUILD_ID.isdigit():
                guild = discord.Object(id=int(config.GUILD_ID))

                # Now setup commands fresh
                logger.info("📝 Setting up commands...")
                setup_commands(self.tree, self.db)

                # Sync to guild
                logger.info(f"🔄 Syncing commands to guild {config.GUILD_ID}...")
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)

                logger.info(f"✅ Commands synced to guild {config.GUILD_ID}")
            else:
                # Setup commands
                setup_commands(self.tree, self.db)

                # No guild specified, sync globally
                self.tree.clear_commands(guild=None)
                await self.tree.sync()
                logger.info(
                    "✅ Commands synced globally (this may take up to 1 hour to propagate)"
                )

            self.synced = True


def main():
    # Check if token is configured
    if not config.TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in .env file!")
        logger.error("Please create a .env file with your Discord bot token.")
        return

    logger.info("🤖 Starting Bonus Points Bot...")

    # Initialize database
    logger.info("📊 Initializing database...")
    db = Database()

    # Initialize bot
    logger.info("🔌 Connecting to Discord...")
    bot = BonusPointsBot(db)

    # Daily reset task
    @tasks.loop(time=time(hour=7, minute=0, tzinfo=pytz.timezone("Europe/Moscow")))
    async def daily_reset():
        logger.info("🔄 Daily reset executed")

    @bot.event
    async def on_ready():
        logger.info(f"✅ Logged in as {bot.user}")
        logger.info(f"📡 Connected to {len(bot.guilds)} server(s)")
        logger.info("⏰ Daily reset scheduled for 07:00 Moscow Time")

        if not daily_reset.is_running():
            daily_reset.start()

        logger.info("🎉 Bot is ready to use!")

    # Optionally add file logging
    file_handler = logging.FileHandler("bot.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logging.getLogger().addHandler(file_handler)

    # Run bot - pass log_handler=None to prevent discord.py from setting up logging again
    try:
        bot.run(config.TOKEN, log_handler=None)
    except KeyboardInterrupt:
        logger.info("👋 Bot shutdown requested")
    except Exception as e:
        logger.exception(f"💥 Fatal error: {e}")


if __name__ == "__main__":
    main()
