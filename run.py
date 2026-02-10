#!/usr/bin/env python3
"""
Bonus Points Web Dashboard
Main entry point for running the web server.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Setup logging
def setup_logging():
    """Configure logging for the web dashboard."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    # Create formatters
    detailed_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # File handler - detailed logging with rotation
    file_handler = RotatingFileHandler(
        log_dir / "web.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)

    # Console handler - cleaner output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Get logger for our app
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Logging system initialized")
    logger.info("=" * 80)

    return logger


def main():
    """Main entry point."""
    logger = setup_logging()

    logger.info("=" * 80)
    logger.info("🚀 Starting Bonus Points Web Dashboard")
    logger.info("=" * 80)

    # Ensure data directory exists
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)

    # Run web server
    from web.app import run_web
    run_web()

    logger.info("=" * 80)
    logger.info("👋 Web dashboard has stopped")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
