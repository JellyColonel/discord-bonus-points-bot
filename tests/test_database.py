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


def test_completed_activities_with_bp_includes_timestamp(db):
    """completed_at should be returned in the third tuple element."""
    user_id = 7001
    date = "2025-01-15"

    db.set_activity_status(user_id, "fishing", date, True, bp_earned=4)

    results = db.get_user_completed_activities_with_bp(user_id, date)
    assert len(results) == 1
    activity_id, bp_earned, completed_at = results[0]
    assert activity_id == "fishing"
    assert bp_earned == 4
    assert completed_at is not None
    assert "T" in completed_at  # ISO format


def test_repeatable_completions_add_remove(db):
    """Add and remove repeatable completions."""
    user_id = 8001
    date = "2025-01-15"

    # Add 3 completions
    count1 = db.add_repeatable_completion(user_id, "online_3h", date, 2)
    assert count1 == 1

    count2 = db.add_repeatable_completion(user_id, "online_3h", date, 4)
    assert count2 == 2

    count3 = db.add_repeatable_completion(user_id, "online_3h", date, 2)
    assert count3 == 3

    # Check grouped data
    data = db.get_repeatable_completions(user_id, date)
    assert "online_3h" in data
    assert len(data["online_3h"]) == 3
    total_bp = sum(bp for bp, _ in data["online_3h"])
    assert total_bp == 8

    # Remove most recent
    new_count, removed_bp = db.remove_repeatable_completion(user_id, "online_3h", date)
    assert new_count == 2
    assert removed_bp == 2  # Last added was 2 BP

    # Remove from empty activity
    empty_count, empty_bp = db.remove_repeatable_completion(user_id, "nonexistent", date)
    assert empty_count == 0
    assert empty_bp == 0


def test_reset_today_activities(db):
    """Reset should clear both regular and repeatable completions."""
    user_id = 9001
    date = "2025-01-15"

    # Add regular completions
    db.set_activity_status(user_id, "fishing", date, True, bp_earned=4)
    db.set_activity_status(user_id, "metro", date, True, bp_earned=2)

    # Add repeatable completions
    db.add_repeatable_completion(user_id, "online_3h", date, 2)
    db.add_repeatable_completion(user_id, "online_3h", date, 2)

    # Reset
    regular_deleted, repeatable_deleted = db.reset_today_activities(user_id, date)
    assert regular_deleted == 2
    assert repeatable_deleted == 2

    # Verify empty
    assert db.get_activity_status(user_id, "fishing", date) is False
    data = db.get_repeatable_completions(user_id, date)
    assert len(data) == 0


# ============================================================================
# Settings
# ============================================================================


def test_get_set_setting(db):
    """Setting round-trip should work."""
    assert db.get_setting("theme") is None
    assert db.get_setting("theme", "dark") == "dark"

    db.set_setting("theme", "light")
    assert db.get_setting("theme") == "light"

    # Overwrite
    db.set_setting("theme", "dark")
    assert db.get_setting("theme") == "dark"


# ============================================================================
# is_activity_hidden
# ============================================================================


def test_is_activity_hidden(db):
    """Direct hidden check should work."""
    user_id = 10001
    assert db.is_activity_hidden(user_id, "fishing") is False

    db.hide_activity(user_id, "fishing")
    assert db.is_activity_hidden(user_id, "fishing") is True

    db.unhide_activity(user_id, "fishing")
    assert db.is_activity_hidden(user_id, "fishing") is False


# ============================================================================
# get_user_completed_activities (without BP)
# ============================================================================


def test_get_user_completed_activities(db):
    """Should return completed activity IDs for a date."""
    user_id = 11001
    date = "2025-02-01"

    # No completions
    assert db.get_user_completed_activities(user_id, date) == []

    # Add some
    db.set_activity_status(user_id, "fishing", date, True, bp_earned=4)
    db.set_activity_status(user_id, "metro", date, True, bp_earned=2)
    db.set_activity_status(user_id, "darts", date, False)  # Not completed

    completed = db.get_user_completed_activities(user_id, date)
    assert set(completed) == {"fishing", "metro"}
    assert "darts" not in completed


# ============================================================================
# get_activity_bp_earned
# ============================================================================


def test_get_activity_bp_earned(db):
    """Should return stored BP or None."""
    user_id = 12001
    date = "2025-02-01"

    # Not completed
    assert db.get_activity_bp_earned(user_id, "fishing", date) is None

    # Completed with BP
    db.set_activity_status(user_id, "fishing", date, True, bp_earned=8)
    assert db.get_activity_bp_earned(user_id, "fishing", date) == 8

    # Uncompleted — should return None
    db.set_activity_status(user_id, "fishing", date, False)
    assert db.get_activity_bp_earned(user_id, "fishing", date) is None


# ============================================================================
# delete_repeatable_completions_for_date
# ============================================================================


def test_delete_repeatable_completions_for_date(db):
    """Should delete all repeatable completions for a specific date."""
    user_id = 13001
    date = "2025-02-01"
    other_date = "2025-02-02"

    db.add_repeatable_completion(user_id, "online_3h", date, 2)
    db.add_repeatable_completion(user_id, "online_3h", date, 2)
    db.add_repeatable_completion(user_id, "online_3h", other_date, 2)

    deleted = db.delete_repeatable_completions_for_date(user_id, date)
    assert deleted == 2

    # Date should be empty, other_date untouched
    assert len(db.get_repeatable_completions(user_id, date)) == 0
    assert len(db.get_repeatable_completions(user_id, other_date)["online_3h"]) == 1


# ============================================================================
# VIP / Event toggle
# ============================================================================


def test_set_vip_and_event_status(db):
    """VIP and event toggles should persist."""
    user_id = 14001

    db.set_user_vip_status(user_id, True)
    assert db.get_user_vip_status(user_id) is True

    db.set_user_vip_status(user_id, False)
    assert db.get_user_vip_status(user_id) is False

    db.set_user_event_status(user_id, True)
    assert db.get_user_event_status(user_id) is True

    db.set_user_event_status(user_id, False)
    assert db.get_user_event_status(user_id) is False


# ============================================================================
# close_connection
# ============================================================================


def test_close_connection(db):
    """Closing should be safe, even when called multiple times."""
    # Force a connection to be created
    db.get_connection()
    db.close_connection()
    db.close_connection()  # Second close should not error

    # Should still work after reopen
    assert db.get_user_bp_balance(99999) == 0


# ============================================================================
# user_exists / ensure_user_exists
# ============================================================================


def test_user_exists(db):
    """user_exists should return False for unknown user, True after row created."""
    user_id = 15001
    assert db.user_exists(user_id) is False

    db.set_user_bp_balance(user_id, 0)  # Creates user row
    assert db.user_exists(user_id) is True


def test_ensure_user_exists(db):
    """ensure_user_exists should create row with defaults, be idempotent."""
    user_id = 16001
    assert db.user_exists(user_id) is False

    db.ensure_user_exists(user_id)
    assert db.user_exists(user_id) is True
    assert db.get_user_bp_balance(user_id) == 0
    assert db.get_user_vip_status(user_id) is False
    assert db.get_user_event_status(user_id) is False

    # Idempotent — second call should not error or change data
    db.set_user_bp_balance(user_id, 100)
    db.ensure_user_exists(user_id)
    assert db.get_user_bp_balance(user_id) == 100
