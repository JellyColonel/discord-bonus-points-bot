# bonus_points_bot/bot/commands/__init__.py
"""Command modules for the bot."""

from bot.commands.activities import setup_activity_commands
from bot.commands.admin import setup_admin_commands
from bot.commands.balance import setup_balance_commands
from bot.commands.help import setup_help_command


def setup_all_commands(tree, db, config):
    """Setup all bot commands."""
    setup_help_command(tree, db, config)
    setup_activity_commands(tree, db, config)
    setup_balance_commands(tree, db, config)
    setup_admin_commands(tree, db, config)


__all__ = [
    "setup_all_commands",
    "setup_activity_commands",
    "setup_balance_commands",
    "setup_admin_commands",
    "setup_help_command",
]
