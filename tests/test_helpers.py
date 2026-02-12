"""Tests for helper functions."""

from datetime import datetime, timedelta, timezone

from web.helpers import (
    RETURNING_USER_THRESHOLD_DAYS,
    calculate_bp,
    get_hidden_activity_ids,
    is_activity_visible,
    is_returning_user,
)

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


# ============================================================================
# is_returning_user
# ============================================================================


def test_is_returning_user_new_user(db):
    """New user (no row) should return False — onboarding takes priority."""
    assert is_returning_user(db, 60001) is False


def test_is_returning_user_recent_login(db):
    """User who logged in recently should return False."""
    user_id = 60002
    db.ensure_user_exists(user_id)
    db.update_last_login(user_id)  # Sets to now

    assert is_returning_user(db, user_id) is False


def test_is_returning_user_old_login(db):
    """User who logged in 15 days ago should return True."""
    user_id = 60003
    db.ensure_user_exists(user_id)

    # Manually set last_login to 15 days ago
    old_time = (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()
    with db.get_cursor() as cursor:
        cursor.execute(
            "UPDATE users SET last_login_at = ? WHERE user_id = ?",
            (old_time, str(user_id)),
        )

    assert is_returning_user(db, user_id) is True


def test_is_returning_user_boundary(db):
    """Exactly 14 days should trigger, 13 days should not."""
    user_id_14 = 60004
    user_id_13 = 60005

    db.ensure_user_exists(user_id_14)
    db.ensure_user_exists(user_id_13)

    # 14 days ago → should trigger
    time_14 = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()
    with db.get_cursor() as cursor:
        cursor.execute(
            "UPDATE users SET last_login_at = ? WHERE user_id = ?",
            (time_14, str(user_id_14)),
        )

    assert is_returning_user(db, user_id_14) is True

    # 13 days ago → should NOT trigger
    time_13 = (datetime.now(timezone.utc) - timedelta(days=13)).isoformat()
    with db.get_cursor() as cursor:
        cursor.execute(
            "UPDATE users SET last_login_at = ? WHERE user_id = ?",
            (time_13, str(user_id_13)),
        )

    assert is_returning_user(db, user_id_13) is False
