"""Helper functions for the web dashboard."""


def is_event_active(db) -> bool:
    """Check if double BP event is currently active.

    Note: This queries the database. If calling multiple times in same request,
    fetch once and reuse the boolean value.

    Args:
        db: Database instance

    Returns:
        True if x2 BP event is active, False otherwise
    """
    event_active = db.get_setting("double_bp_event", "False")
    return event_active == "True"


def calculate_bp(activity: dict, vip_status: bool, event_active: bool) -> int:
    """Calculate BP for an activity considering VIP and event status.

    Args:
        activity: Activity dictionary with 'bp' and 'bp_vip' keys
        vip_status: Boolean indicating if user has VIP
        event_active: Boolean indicating if x2 BP event is active

    Returns:
        Calculated BP amount
    """
    base_bp = activity["bp_vip"] if vip_status else activity["bp"]
    multiplier = 2 if event_active else 1
    return base_bp * multiplier
