"""Tests for helper functions."""

from datetime import datetime, timedelta, timezone

from web.helpers import (
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


# ============================================================================
# prepare_recipes_data
# ============================================================================


def test_prepare_recipes_data_returns_recipes():
    """Should return a dict with 'recipes' key containing all recipes."""
    from web.helpers import prepare_recipes_data
    from web.recipes import RECIPES

    data = prepare_recipes_data()
    assert "recipes" in data
    assert len(data["recipes"]) == len(RECIPES)


def test_prepare_recipes_data_simple_recipe():
    """Simple recipe (no sub-recipes) should have 1 step and empty steps list."""
    from web.helpers import prepare_recipes_data

    data = prepare_recipes_data()
    # Find scrambled_eggs (a simple recipe)
    scrambled = next(r for r in data["recipes"] if r["id"] == "scrambled_eggs")

    assert scrambled["step_count"] == 1
    assert scrambled["steps"] == []
    assert scrambled["final_step"]["id"] == "scrambled_eggs"
    assert len(scrambled["final_step"]["ingredients"]) == 3
    assert len(scrambled["final_step"]["tools"]) == 1


def test_prepare_recipes_data_chained_recipe():
    """Chained recipe should have sub-recipe steps in order."""
    from web.helpers import prepare_recipes_data

    data = prepare_recipes_data()
    # mac_and_cheese → macaroni → dough (2 sub-steps + 1 final = 3 steps)
    mac = next(r for r in data["recipes"] if r["id"] == "mac_and_cheese")

    assert mac["step_count"] == 3
    assert len(mac["steps"]) == 2
    step_ids = [s["id"] for s in mac["steps"]]
    assert step_ids.index("dough") < step_ids.index("macaroni")
    assert mac["final_step"]["id"] == "mac_and_cheese"


def test_prepare_recipes_data_shopping_list():
    """Shopping list should contain only store-type ingredients."""
    from web.helpers import prepare_recipes_data

    data = prepare_recipes_data()
    lemonade = next(r for r in data["recipes"] if r["id"] == "lemonade")

    shopping_ids = {item["id"] for item in lemonade["shopping_list"]}
    assert "lemon" in shopping_ids
    assert "sugar" in shopping_ids
    assert "water" not in shopping_ids  # default type, not store


def test_prepare_recipes_data_all_tools():
    """All tools should include tools from sub-recipes."""
    from web.helpers import prepare_recipes_data

    data = prepare_recipes_data()
    macaroni = next(r for r in data["recipes"] if r["id"] == "macaroni")

    tool_ids = {t["id"] for t in macaroni["all_tools"]}
    assert tool_ids == {"whisk", "knife", "fire"}


def test_prepare_recipes_data_ingredient_is_recipe_flag():
    """Ingredients that are recipes should have is_recipe=True."""
    from web.helpers import prepare_recipes_data

    data = prepare_recipes_data()
    macaroni = next(r for r in data["recipes"] if r["id"] == "macaroni")

    ings = macaroni["final_step"]["ingredients"]
    dough_ing = next(i for i in ings if i["id"] == "dough")
    water_ing = next(i for i in ings if i["id"] == "water")

    assert dough_ing["is_recipe"] is True
    assert water_ing["is_recipe"] is False
