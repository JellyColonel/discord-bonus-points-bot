#!/usr/bin/env python3
"""
Discord Bonus Points Bot + Web Dashboard
Main entry point for running both the bot and web server.
"""

import logging
from threading import Thread

logger = logging.getLogger(__name__)


def run_bot():
    """Run the Discord bot."""
    from bot.main import main

    main()


def run_web_server():
    """Run the web dashboard."""
    from web.app import run_web

    run_web()


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("🚀 Starting Bonus Points Bot + Web Dashboard")
    logger.info("=" * 80)

    # Start web server in background thread
    web_thread = Thread(target=run_web_server, daemon=True, name="WebDashboard")
    web_thread.start()
    logger.info("✅ Web dashboard thread started")

    # Start bot (this blocks until bot stops)
    logger.info("🤖 Starting Discord bot...")
    run_bot()

    logger.info("=" * 80)
    logger.info("👋 Both bot and web dashboard have stopped")
    logger.info("=" * 80)
