#!/usr/bin/env python3
"""
Discord Bonus Points Bot
Main entry point for running the bot.
"""

import sys
from pathlib import Path

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent / 'bot'))

from bot.main import main

if __name__ == "__main__":
    main()
