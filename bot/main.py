# bonus_points_bot/bot/main.py
"""Main bot module."""

import logging
from pathlib import Path

from bot.core.bot import BonusPointsBot
from bot.core.config import Config
from bot.core.database import Database


# Setup logging configuration
def setup_logging():
    """Configure logging for the bot."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s | %(name)-25s | %(funcName)-20s:%(lineno)-4d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # File handler - detailed logging
    file_handler = logging.FileHandler(log_dir / "bot.log", encoding="utf-8", mode="a")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Console handler - cleaner output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Reduce HTTP spam from discord.py
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    logging.getLogger("discord.gateway").setLevel(logging.INFO)
    logging.getLogger("discord.client").setLevel(logging.INFO)

    # Production logging levels
    logging.getLogger("bot.core.database").setLevel(logging.INFO)
    logging.getLogger("bot.commands").setLevel(logging.INFO)
    # Keep bot core at DEBUG for important startup/shutdown info
    logging.getLogger("bot.core.bot").setLevel(logging.INFO)

    # Get logger for our bot
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Logging system initialized")
    logger.info("=" * 80)

    return logger


def main():
    """Main entry point for the bot."""
    logger = setup_logging()

    # Load configuration
    logger.info("📝 Loading configuration...")
    config = Config()

    # Check if token is configured
    if not config.TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in .env file!")
        logger.error("Please create a .env file with your Discord bot token.")
        return

    logger.info("🤖 Starting Bonus Points Bot...")
    logger.info(
        f"Guild ID: {config.GUILD_ID if config.GUILD_ID else 'Not set (global sync)'}"
    )
    logger.info(
        f"Admin Role ID: {config.ADMIN_ROLE_ID if config.ADMIN_ROLE_ID and config.ADMIN_ROLE_ID != 'your_admin_role_id_here' else 'Not set'}"
    )

    # Initialize database
    logger.info("📊 Initializing database...")
    db_path = Path(__file__).parent.parent / "data" / "bonus_points.db"
    db_path.parent.mkdir(exist_ok=True)
    db = Database(str(db_path))
    logger.info(f"📊 Database initialized at: {db_path}")

    # Initialize and run bot
    logger.info("🔌 Connecting to Discord...")
    bot = BonusPointsBot(db, config)

    try:
        bot.run(config.TOKEN, log_handler=None)
    except KeyboardInterrupt:
        logger.info("👋 Bot shutdown requested by user")
    except Exception as e:
        logger.exception(f"💥 Fatal error: {e}")
    finally:
        logger.info("🛑 Bot has stopped")


if __name__ == "__main__":
    main()
