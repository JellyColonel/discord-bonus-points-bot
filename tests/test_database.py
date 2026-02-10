"""Tests for database operations."""

import threading


def test_add_user_bp_atomic(db):
    """Concurrent balance updates should not lose data."""
    user_id = 1001
    db.set_user_bp_balance(user_id, 0)

    errors = []

    def add_bp():
        try:
            for _ in range(50):
                db.add_user_bp(user_id, 1)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=add_bp) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Threads raised errors: {errors}"
    balance = db.get_user_bp_balance(user_id)
    assert balance == 200, f"Expected 200, got {balance} (lost updates)"


def test_subtract_bp_floor_zero(db):
    """Balance should never go negative."""
    user_id = 2001
    db.set_user_bp_balance(user_id, 10)

    new_balance = db.subtract_user_bp(user_id, 50)
    assert new_balance == 0

    stored_balance = db.get_user_bp_balance(user_id)
    assert stored_balance == 0


def test_add_user_bp_returns_new_balance(db):
    """add_user_bp should return the updated balance."""
    user_id = 3001
    db.set_user_bp_balance(user_id, 100)

    new_balance = db.add_user_bp(user_id, 25)
    assert new_balance == 125


def test_set_activity_status_idempotent(db):
    """Toggling the same activity multiple times should be safe."""
    user_id = 4001
    activity_id = "test_activity"
    date = "2025-01-01"

    # Complete twice
    db.set_activity_status(user_id, activity_id, date, True, bp_earned=5)
    db.set_activity_status(user_id, activity_id, date, True, bp_earned=5)

    assert db.get_activity_status(user_id, activity_id, date) is True
    assert db.get_activity_bp_earned(user_id, activity_id, date) == 5

    # Uncomplete twice
    db.set_activity_status(user_id, activity_id, date, False)
    db.set_activity_status(user_id, activity_id, date, False)

    assert db.get_activity_status(user_id, activity_id, date) is False


def test_hidden_activities(db):
    """Hide/unhide round-trip should work."""
    user_id = 5001

    assert db.hide_activity(user_id, "fishing") is True
    assert db.hide_activity(user_id, "fishing") is False  # Already hidden

    hidden = db.get_hidden_activities(user_id)
    assert "fishing" in hidden

    assert db.unhide_activity(user_id, "fishing") is True
    assert db.unhide_activity(user_id, "fishing") is False  # Already visible

    hidden = db.get_hidden_activities(user_id)
    assert "fishing" not in hidden


def test_vip_and_event_defaults(db):
    """New users should have VIP and event off by default."""
    user_id = 6001

    assert db.get_user_vip_status(user_id) is False
    assert db.get_user_event_status(user_id) is False
    assert db.get_user_bp_balance(user_id) == 0
