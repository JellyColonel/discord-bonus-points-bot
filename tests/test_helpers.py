"""Tests for helper functions."""

from web.helpers import calculate_bp, get_hidden_activity_ids, is_activity_visible

# ============================================================================
# calculate_bp
# ============================================================================


def test_calculate_bp_base():
    """Base BP without multipliers."""
    activity = {"bp": 4}
    assert calculate_bp(activity, vip_status=False, event_active=False) == 4


def test_calculate_bp_vip():
    """VIP doubles BP."""
    activity = {"bp": 4}
    assert calculate_bp(activity, vip_status=True, event_active=False) == 8


def test_calculate_bp_event():
    """Event doubles BP."""
    activity = {"bp": 4}
    assert calculate_bp(activity, vip_status=False, event_active=True) == 8


def test_calculate_bp_vip_and_event():
    """VIP + event = 4x multiplier."""
    activity = {"bp": 4}
    assert calculate_bp(activity, vip_status=True, event_active=True) == 16


def test_calculate_bp_1bp_activity():
    """1 BP activity with multipliers."""
    activity = {"bp": 1}
    assert calculate_bp(activity, vip_status=False, event_active=False) == 1
    assert calculate_bp(activity, vip_status=True, event_active=True) == 4


# ============================================================================
# is_activity_visible / get_hidden_activity_ids
# ============================================================================


def test_is_activity_visible_not_hidden():
    """Activity not in hidden set should be visible."""
    activity = {"id": "fishing"}
    assert is_activity_visible(activity, set()) is True
    assert is_activity_visible(activity, {"metro", "darts"}) is True


def test_is_activity_visible_hidden():
    """Activity in hidden set should not be visible."""
    activity = {"id": "fishing"}
    assert is_activity_visible(activity, {"fishing"}) is False


def test_get_hidden_activity_ids_from_db(db):
    """Should return set of hidden IDs from database."""
    user_id = 50001
    db.hide_activity(user_id, "fishing")
    db.hide_activity(user_id, "metro")

    hidden = get_hidden_activity_ids(db, user_id)
    assert hidden == {"fishing", "metro"}


def test_get_hidden_activity_ids_preloaded(db):
    """Should use pre-fetched list when provided."""
    hidden = get_hidden_activity_ids(db, 99999, hidden_activities=["a", "b"])
    assert hidden == {"a", "b"}
