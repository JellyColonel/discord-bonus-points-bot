"""Helper functions for the bot."""

import discord


def get_bp_multiplier(db):
    """Get current BP multiplier based on event status."""
    # Check database first (persistent), then fall back to config
    event_active = db.get_setting("double_bp_event", "False")
    return 2 if event_active == "True" else 1


def is_event_active(db):
    """Check if double BP event is currently active."""
    event_active = db.get_setting("double_bp_event", "False")
    return event_active == "True"


def calculate_bp(activity, vip_status, db):
    """Calculate BP for an activity considering VIP and event multiplier."""
    base_bp = activity["bp_vip"] if vip_status else activity["bp"]
    multiplier = get_bp_multiplier(db)
    return base_bp * multiplier


def has_admin_role(interaction: discord.Interaction, config) -> bool:
    """Check if user has admin role."""
    # First check for administrator permission
    if interaction.user.guild_permissions.administrator:
        return True

    # Then check for admin role if configured with a valid ID
    if config.ADMIN_ROLE_ID and config.ADMIN_ROLE_ID.isdigit():
        admin_role = discord.utils.get(
            interaction.user.roles, id=int(config.ADMIN_ROLE_ID)
        )
        return admin_role is not None

    return False
