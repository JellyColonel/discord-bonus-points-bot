"""Tests for API endpoints."""

import json
from datetime import datetime, timedelta, timezone


def test_toggle_activity_unauthenticated(client):
    """Unauthenticated requests should redirect to login."""
    response = client.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "fishing", "completed": True}),
        content_type="application/json",
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_toggle_activity_success(auth_session):
    """Completing and uncompleting an activity should update balance."""
    # Complete
    response = auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "fishing", "completed": True}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["bp_change"] > 0
    balance_after_complete = data["new_balance"]

    # Uncomplete
    response = auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "fishing", "completed": False}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["bp_change"] < 0
    assert data["new_balance"] == balance_after_complete + data["bp_change"]


def test_toggle_activity_invalid_id(auth_session):
    """Invalid activity ID should return 404."""
    response = auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "nonexistent_activity", "completed": True}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is False
    assert response.status_code == 404


def test_set_balance_validation(auth_session):
    """Balance endpoint should reject invalid values."""
    # Negative
    response = auth_session.post(
        "/api/set_balance",
        data=json.dumps({"amount": -1}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is False

    # Over 1M
    response = auth_session.post(
        "/api/set_balance",
        data=json.dumps({"amount": 1000001}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is False

    # Valid
    response = auth_session.post(
        "/api/set_balance",
        data=json.dumps({"amount": 500}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["new_balance"] == 500


def test_toggle_vip(auth_session):
    """VIP toggle should return updated status."""
    response = auth_session.post(
        "/api/toggle_vip",
        data=json.dumps({"vip_status": True}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["vip_status"] is True


def test_toggle_event(auth_session):
    """Event toggle should return updated status."""
    response = auth_session.post(
        "/api/toggle_event",
        data=json.dumps({"event_status": True}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["event_status"] is True


def test_hide_unhide_activity(auth_session):
    """Hide/unhide flow should work end-to-end."""
    # Hide
    response = auth_session.post(
        "/api/hide_activity",
        data=json.dumps({"activity_id": "fishing"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["hidden"] is True

    # Verify hidden
    response = auth_session.get("/api/hidden_items")
    data = json.loads(response.data)
    assert "fishing" in data["hidden_activities"]

    # Unhide
    response = auth_session.post(
        "/api/unhide_activity",
        data=json.dumps({"activity_id": "fishing"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["hidden"] is False


def test_user_stats(auth_session):
    """User stats endpoint should return expected fields."""
    response = auth_session.get("/api/user_stats")
    data = json.loads(response.data)
    assert data["success"] is True
    assert "balance" in data
    assert "total_earned" in data
    assert "total_remaining" in data
    assert "completed_count" in data
    assert "total_activities" in data


def test_rate_limit_enforced(auth_session):
    """Exceeding rate limit should return 429."""
    # The set_balance endpoint has 10 req/min limit
    for _ in range(11):
        response = auth_session.post(
            "/api/set_balance",
            data=json.dumps({"amount": 100}),
            content_type="application/json",
        )

    assert response.status_code == 429


def test_toggle_activity_returns_completed_at(auth_session):
    """Completing an activity should return completed_at timestamp."""
    response = auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "metro", "completed": True}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert "completed_at" in data
    assert "T" in data["completed_at"]  # ISO format


def test_repeatable_activity_add_remove(auth_session):
    """Repeatable activity add/remove should work."""
    # Add
    response = auth_session.post(
        "/api/repeatable_activity",
        data=json.dumps({"activity_id": "online_3h", "action": "add"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["count"] == 1
    assert data["bp_change"] > 0
    assert "completed_at" in data
    _ = data["new_balance"]  # balance changes tested in other assertions

    # Add again
    response = auth_session.post(
        "/api/repeatable_activity",
        data=json.dumps({"activity_id": "online_3h", "action": "add"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["count"] == 2

    # Remove
    response = auth_session.post(
        "/api/repeatable_activity",
        data=json.dumps({"activity_id": "online_3h", "action": "remove"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["count"] == 1
    assert data["bp_change"] < 0


def test_repeatable_activity_cap_enforced(auth_session):
    """Repeatable activity should reject additions beyond max_completions."""
    from web.helpers import _rate_limit_store
    _rate_limit_store.clear()

    from web.activities import get_activity_by_id
    activity = get_activity_by_id("online_3h")
    max_completions = activity["max_completions"]

    # Add up to the cap
    for i in range(max_completions):
        response = auth_session.post(
            "/api/repeatable_activity",
            data=json.dumps({"activity_id": "online_3h", "action": "add"}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["count"] == i + 1

    # One more should fail
    response = auth_session.post(
        "/api/repeatable_activity",
        data=json.dumps({"activity_id": "online_3h", "action": "add"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is False
    assert "лимит" in data["error"].lower()

    # Remove one, then adding should work again
    response = auth_session.post(
        "/api/repeatable_activity",
        data=json.dumps({"activity_id": "online_3h", "action": "remove"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["count"] == max_completions - 1

    response = auth_session.post(
        "/api/repeatable_activity",
        data=json.dumps({"activity_id": "online_3h", "action": "add"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["count"] == max_completions


def test_repeatable_activity_non_repeatable_rejected(auth_session):
    """Non-repeatable activities should be rejected."""
    response = auth_session.post(
        "/api/repeatable_activity",
        data=json.dumps({"activity_id": "fishing", "action": "add"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is False
    assert "not repeatable" in data["error"]


def test_reset_today_activities(auth_session):
    """Reset endpoint should clear completions."""
    # Clear rate limit store from previous tests
    from web.helpers import _rate_limit_store
    _rate_limit_store.clear()

    # Complete some activities first
    auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "darts", "completed": True}),
        content_type="application/json",
    )

    # Reset
    response = auth_session.post(
        "/api/reset_today_activities",
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert "deleted_count" in data
    assert "balance" in data


# ============================================================================
# Missing body / edge cases
# ============================================================================


def test_toggle_activity_missing_body(auth_session):
    """Missing JSON body should return 400."""
    response = auth_session.post(
        "/api/toggle_activity",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_repeatable_activity_missing_body(auth_session):
    """Missing JSON body should return 400."""
    response = auth_session.post(
        "/api/repeatable_activity",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_repeatable_activity_invalid_action(auth_session):
    """Invalid action should return error."""
    response = auth_session.post(
        "/api/repeatable_activity",
        data=json.dumps({"activity_id": "online_3h", "action": "invalid"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is False
    assert "action" in data["error"]


def test_repeatable_remove_zero_completions(auth_session):
    """Removing with 0 completions should return error."""
    response = auth_session.post(
        "/api/repeatable_activity",
        data=json.dumps({"activity_id": "online_3h", "action": "remove"}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is False
    assert "No completions" in data["error"]


def test_toggle_activity_hidden_rejected(auth_session):
    """Toggling a hidden activity should be rejected."""
    # Hide the activity first
    auth_session.post(
        "/api/hide_activity",
        data=json.dumps({"activity_id": "metro"}),
        content_type="application/json",
    )

    # Try to toggle it
    response = auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "metro", "completed": True}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is False
    assert "hidden" in data["error"].lower()

    # Clean up
    auth_session.post(
        "/api/unhide_activity",
        data=json.dumps({"activity_id": "metro"}),
        content_type="application/json",
    )


def test_set_balance_missing_body(auth_session):
    """Missing JSON body should return 400."""
    response = auth_session.post(
        "/api/set_balance",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_toggle_vip_missing_body(auth_session):
    """Missing JSON body should return 400."""
    response = auth_session.post(
        "/api/toggle_vip",
        content_type="application/json",
    )
    assert response.status_code == 400


def test_toggle_event_missing_body(auth_session):
    """Missing JSON body should return 400."""
    response = auth_session.post(
        "/api/toggle_event",
        content_type="application/json",
    )
    assert response.status_code == 400


# ============================================================================
# Untested endpoints
# ============================================================================


def test_user_data_endpoint(auth_session):
    """user_data endpoint should return all expected fields."""
    response = auth_session.get("/api/user_data")
    data = json.loads(response.data)
    assert data["success"] is True
    assert "vip_status" in data
    assert "balance" in data
    assert "completed_activities" in data
    assert "event_active" in data
    assert "hidden_activities" in data


def test_activity_bp_values_endpoint(auth_session):
    """activity_bp_values endpoint should return BP map and totals."""
    response = auth_session.get("/api/activity_bp_values")
    data = json.loads(response.data)
    assert data["success"] is True
    assert "activities" in data
    assert "total_earned" in data
    assert "total_remaining" in data
    assert isinstance(data["activities"], dict)
    assert len(data["activities"]) > 0


def test_vip_affects_bp_calculation(auth_session):
    """Enabling VIP should double BP earned on activity completion."""
    from web.helpers import _rate_limit_store
    _rate_limit_store.clear()

    # Enable VIP
    auth_session.post(
        "/api/toggle_vip",
        data=json.dumps({"vip_status": True}),
        content_type="application/json",
    )

    # Complete an activity (fishing = 4 BP base)
    response = auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "fishing", "completed": True}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["bp_change"] == 8  # 4 * 2 (VIP)

    # Clean up: uncomplete and disable VIP
    auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "fishing", "completed": False}),
        content_type="application/json",
    )
    auth_session.post(
        "/api/toggle_vip",
        data=json.dumps({"vip_status": False}),
        content_type="application/json",
    )


def test_event_affects_bp_calculation(auth_session):
    """Enabling event should double BP earned on activity completion."""
    from web.helpers import _rate_limit_store
    _rate_limit_store.clear()

    # Enable event
    auth_session.post(
        "/api/toggle_event",
        data=json.dumps({"event_status": True}),
        content_type="application/json",
    )

    # Complete an activity (basketball = 1 BP base)
    response = auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "basketball", "completed": True}),
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True
    assert data["bp_change"] == 2  # 1 * 2 (event)

    # Clean up
    auth_session.post(
        "/api/toggle_activity",
        data=json.dumps({"activity_id": "basketball", "completed": False}),
        content_type="application/json",
    )
    auth_session.post(
        "/api/toggle_event",
        data=json.dumps({"event_status": False}),
        content_type="application/json",
    )


# ============================================================================
# Onboarding
# ============================================================================


def test_complete_onboarding_creates_user_row(auth_session):
    """POST /api/complete_onboarding should create user row and return success."""
    response = auth_session.post(
        "/api/complete_onboarding",
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True


def test_complete_onboarding_unauthenticated(client):
    """Unauthenticated onboarding request should redirect to login."""
    response = client.post(
        "/api/complete_onboarding",
        content_type="application/json",
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_dashboard_shows_onboarding_for_new_user(auth_session):
    """New user dashboard should contain onboarding overlay."""
    response = auth_session.get("/dashboard")
    assert response.status_code == 200
    assert b"onboarding-overlay" in response.data


def test_dashboard_hides_onboarding_for_existing_user(auth_session):
    """After completing onboarding, dashboard should NOT contain overlay."""
    # Complete onboarding (creates user row)
    auth_session.post(
        "/api/complete_onboarding",
        content_type="application/json",
    )

    response = auth_session.get("/dashboard")
    assert response.status_code == 200
    assert b"onboarding-overlay" not in response.data


# ============================================================================
# Returning User Reminder
# ============================================================================


def test_dismiss_reminder_success(auth_session):
    """POST /api/dismiss_reminder should return success."""
    response = auth_session.post(
        "/api/dismiss_reminder",
        content_type="application/json",
    )
    data = json.loads(response.data)
    assert data["success"] is True


def test_dismiss_reminder_unauthenticated(client):
    """Unauthenticated dismiss_reminder should redirect to login."""
    response = client.post(
        "/api/dismiss_reminder",
        content_type="application/json",
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_dashboard_shows_reminder_for_returning_user(auth_session):
    """Dashboard should show reminder-overlay when session flag is set."""
    from web.app import db as app_db

    user_id = 123456789  # Same as auth_session fixture

    # Create user with old last_login
    app_db.ensure_user_exists(user_id)
    old_time = (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()
    with app_db.get_cursor() as cursor:
        cursor.execute(
            "UPDATE users SET last_login_at = ? WHERE user_id = ?",
            (old_time, str(user_id)),
        )

    # Set the session flag (simulating what /callback would do)
    with auth_session.session_transaction() as sess:
        sess["show_returning_reminder"] = True

    response = auth_session.get("/dashboard")
    assert response.status_code == 200
    assert b"reminder-overlay" in response.data


def test_dashboard_no_reminder_for_recent_user(auth_session):
    """Dashboard should NOT show reminder for recently logged in user."""
    from web.app import db as app_db

    user_id = 123456789
    app_db.ensure_user_exists(user_id)
    app_db.update_last_login(user_id)

    response = auth_session.get("/dashboard")
    assert response.status_code == 200
    assert b"reminder-overlay" not in response.data
