"""Main bot module."""

import logging
from pathlib import Path

from core.bot import BonusPointsBot
from core.config import Config
from core.database import Database

# Setup logging configuration
def setup_logging():
    """Configure logging for the bot."""
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Setup discord.py's logging
    import discord.utils
    discord.utils.setup_logging(level=logging.INFO, root=True)
    
    # Reduce HTTP spam
    logging.getLogger("discord.http").setLevel(logging.WARNING)
    
    # Get logger for our bot
    logger = logging.getLogger(__name__)
    
    # Add file handler
    file_handler = logging.FileHandler(
        log_dir / "bot.log", 
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logging.getLogger().addHandler(file_handler)
    
    return logger


def main():
    """Main entry point for the bot."""
    logger = setup_logging()
    
    # Load configuration
    config = Config()
    
    # Check if token is configured
    if not config.TOKEN:
        logger.error("❌ DISCORD_TOKEN not found in .env file!")
        logger.error("Please create a .env file with your Discord bot token.")
        return
    
    logger.info("🤖 Starting Bonus Points Bot...")
    
    # Initialize database
    logger.info("📊 Initializing database...")
    db_path = Path(__file__).parent.parent / "data" / "bonus_points.db"
    db_path.parent.mkdir(exist_ok=True)
    db = Database(str(db_path))
    
    # Initialize and run bot
    logger.info("🔌 Connecting to Discord...")
    bot = BonusPointsBot(db, config)
    
    try:
        bot.run(config.TOKEN, log_handler=None)
    except KeyboardInterrupt:
        logger.info("👋 Bot shutdown requested")
    except Exception as e:
        logger.exception(f"💥 Fatal error: {e}")


if __name__ == "__main__":
    main()
