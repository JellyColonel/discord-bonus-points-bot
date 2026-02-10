"""Tests for API endpoints."""

import json


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
    balance_after_add = data["new_balance"]

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
