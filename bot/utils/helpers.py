# bonus_points_bot/bot/utils/helpers.py
"""Helper functions for the bot."""

import discord


def get_bp_multiplier(db):
    """Get current BP multiplier based on event status.

    WARNING: This queries the database. If you already have event_active,
    use get_bp_multiplier_from_status() instead to avoid redundant queries.
    """
    # Check database first (persistent), then fall back to config
    event_active = db.get_setting("double_bp_event", "False")
    return 2 if event_active == "True" else 1


def get_bp_multiplier_from_status(event_active: bool) -> int:
    """Get BP multiplier from pre-fetched event status.

    Use this when you already have event_active to avoid DB queries.

    Args:
        event_active: Boolean indicating if x2 BP event is active

    Returns:
        2 if event is active, 1 otherwise
    """
    return 2 if event_active else 1


def is_event_active(db):
    """Check if double BP event is currently active.

    WARNING: This queries the database. If calling multiple times in same function,
    fetch once and reuse the boolean value.
    """
    event_active = db.get_setting("double_bp_event", "False")
    return event_active == "True"


def calculate_bp(activity, vip_status, db):
    """Calculate BP for an activity considering VIP and event multiplier.

    WARNING: This queries the database for event status. If you already have
    event_active or bp_multiplier, use calculate_bp_fast() instead.

    Args:
        activity: Activity dictionary with 'bp' and 'bp_vip' keys
        vip_status: Boolean indicating if user has VIP
        db: Database instance

    Returns:
        Calculated BP amount
    """
    base_bp = activity["bp_vip"] if vip_status else activity["bp"]
    multiplier = get_bp_multiplier(db)
    return base_bp * multiplier


def calculate_bp_fast(activity, vip_status, bp_multiplier: int):
    """Calculate BP for an activity with pre-calculated multiplier.

    Use this in loops or when you already know the BP multiplier to avoid
    redundant database queries.

    Args:
        activity: Activity dictionary with 'bp' and 'bp_vip' keys
        vip_status: Boolean indicating if user has VIP
        bp_multiplier: Pre-calculated multiplier (1 or 2)

    Returns:
        Calculated BP amount

    Example:
        bp_multiplier = get_bp_multiplier(db)  # Query once
        for activity in activities:
            points = calculate_bp_fast(activity, vip, bp_multiplier)  # No queries
    """
    base_bp = activity["bp_vip"] if vip_status else activity["bp"]
    return base_bp * bp_multiplier


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
