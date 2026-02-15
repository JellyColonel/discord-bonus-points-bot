"""Tests for recipe data model, lookups, and dependency resolution."""

import pytest

from web.recipes import (
    INGREDIENTS,
    RECIPES,
    RecipeValidationError,
    get_all_ingredients,
    get_all_recipes,
    get_all_tools,
    get_ingredient_by_id,
    get_recipe_by_id,
    get_shopping_list,
    get_sub_recipes,
    is_recipe,
    resolve_name,
    validate_recipes,
)

# ============================================================================
# Data Integrity
# ============================================================================


class TestDataIntegrity:
    """Verify that the built-in recipe data passes validation."""

    def test_validate_recipes_passes(self):
        """Built-in data should pass all validation checks."""
        validate_recipes()  # Should not raise

    def test_no_duplicate_ingredient_ids(self):
        ids = [ing["id"] for ing in INGREDIENTS]
        assert len(ids) == len(set(ids))

    def test_no_duplicate_recipe_ids(self):
        ids = [rec["id"] for rec in RECIPES]
        assert len(ids) == len(set(ids))

    def test_no_id_collisions(self):
        """Ingredient and recipe IDs must not overlap."""
        ing_ids = {ing["id"] for ing in INGREDIENTS}
        rec_ids = {rec["id"] for rec in RECIPES}
        assert ing_ids.isdisjoint(rec_ids)

    def test_all_ingredients_have_required_fields(self):
        for ing in INGREDIENTS:
            assert "id" in ing
            assert "name" in ing
            assert "type" in ing
            assert ing["type"] in ("tool", "store", "default", "fishing")

    def test_all_recipes_have_required_fields(self):
        for rec in RECIPES:
            assert "id" in rec
            assert "name" in rec
            assert "ingredients" in rec
            assert len(rec["ingredients"]) > 0


# ============================================================================
# Lookups
# ============================================================================


class TestLookups:
    def test_get_all_recipes(self):
        assert get_all_recipes() is RECIPES

    def test_get_all_ingredients(self):
        assert get_all_ingredients() is INGREDIENTS

    def test_get_recipe_by_id_existing(self):
        recipe = get_recipe_by_id("dough")
        assert recipe is not None
        assert recipe["name"] == "Тесто"

    def test_get_recipe_by_id_missing(self):
        assert get_recipe_by_id("nonexistent") is None

    def test_get_ingredient_by_id_existing(self):
        ing = get_ingredient_by_id("flour")
        assert ing is not None
        assert ing["name"] == "Мука"

    def test_get_ingredient_by_id_missing(self):
        assert get_ingredient_by_id("nonexistent") is None

    def test_is_recipe_true(self):
        assert is_recipe("dough") is True

    def test_is_recipe_false_ingredient(self):
        assert is_recipe("flour") is False

    def test_is_recipe_false_unknown(self):
        assert is_recipe("nonexistent") is False

    def test_resolve_name_recipe(self):
        assert resolve_name("dough") == "Тесто"

    def test_resolve_name_ingredient(self):
        assert resolve_name("flour") == "Мука"

    def test_resolve_name_unknown(self):
        assert resolve_name("nonexistent") == "nonexistent"


# ============================================================================
# Dependency Resolution
# ============================================================================


class TestSubRecipes:
    def test_simple_recipe_no_sub_recipes(self):
        """A recipe with only base ingredients has no sub-recipes."""
        subs = get_sub_recipes("fried_eggs")
        assert subs == []

    def test_one_level_chain(self):
        """Bread depends on dough."""
        subs = get_sub_recipes("bread")
        assert len(subs) == 1
        assert subs[0]["id"] == "dough"

    def test_two_level_chain(self):
        """Cheese sandwich → bread → dough, + cheese (3 sub-recipes)."""
        subs = get_sub_recipes("cheese_sandwich")
        assert len(subs) == 3
        ids = [s["id"] for s in subs]
        # Topological: dough before bread
        assert ids.index("dough") < ids.index("bread")

    def test_multi_branch_chain(self):
        """Burger → bread (→ dough) + meat_cutlet (→ minced_meat + butter)."""
        subs = get_sub_recipes("burger")
        ids = [s["id"] for s in subs]
        assert "dough" in ids
        assert "bread" in ids
        assert "minced_meat" in ids
        assert "butter" in ids
        assert "meat_cutlet" in ids
        assert ids.index("dough") < ids.index("bread")
        assert ids.index("minced_meat") < ids.index("meat_cutlet")
        assert ids.index("butter") < ids.index("meat_cutlet")

    def test_deep_chain(self):
        """Caramel cheesecake → cheesecake (→ dough + cheese) + caramel."""
        subs = get_sub_recipes("caramel_cheesecake")
        ids = [s["id"] for s in subs]
        assert "dough" in ids
        assert "cheese" in ids
        assert "cheesecake" in ids
        assert "caramel" in ids
        assert ids.index("dough") < ids.index("cheesecake")
        assert ids.index("cheese") < ids.index("cheesecake")

    def test_unknown_recipe_returns_empty(self):
        assert get_sub_recipes("nonexistent") == []


class TestShoppingList:
    def test_simple_recipe(self):
        """Fried eggs: just egg (store)."""
        shopping = get_shopping_list("fried_eggs")
        assert shopping == {"egg": 1}

    def test_excludes_non_store(self):
        """Vegetable smoothie has water (default) — not in shopping list."""
        shopping = get_shopping_list("vegetable_smoothie")
        assert "water" not in shopping
        assert shopping == {"vegetables": 1}

    def test_chained_recipe(self):
        """Bread: dough(flour, water, egg) → flour + egg (store only)."""
        shopping = get_shopping_list("bread")
        assert shopping == {"flour": 1, "egg": 1}

    def test_deep_chain_aggregates(self):
        """Cheese sandwich needs bread ingredients + cheese ingredients."""
        shopping = get_shopping_list("cheese_sandwich")
        assert shopping == {"flour": 1, "egg": 1, "milk": 1}

    def test_multi_branch(self):
        """Burger combines bread + meat_cutlet + vegetables ingredients."""
        shopping = get_shopping_list("burger")
        assert shopping == {
            "flour": 1,
            "egg": 1,
            "meat": 1,
            "milk": 1,
            "vegetables": 1,
        }

    def test_unknown_recipe_returns_empty(self):
        assert get_shopping_list("nonexistent") == {}

    def test_fish_mince_shopping_list(self):
        """Fish mince needs any_fish (fishing type, included in shopping list)."""
        shopping = get_shopping_list("fish_mince")
        assert shopping == {"any_fish": 1}


class TestAllTools:
    def test_simple_recipe(self):
        """Fried eggs needs only fire."""
        tools = get_all_tools("fried_eggs")
        assert tools == ["fire"]

    def test_chained_recipe(self):
        """Bread needs whisk (from dough) + fire."""
        tools = get_all_tools("bread")
        assert set(tools) == {"whisk", "fire"}

    def test_deep_chain(self):
        """Cheese sandwich: whisk (dough) + fire (bread, cheese) + knife."""
        tools = get_all_tools("cheese_sandwich")
        assert set(tools) == {"whisk", "fire", "knife"}

    def test_tool_order_is_stable(self):
        """Tools should appear in order of first encounter (depth-first)."""
        tools = get_all_tools("bread")
        # dough's whisk comes first, then bread's fire
        assert tools.index("whisk") < tools.index("fire")

    def test_unknown_recipe_returns_empty(self):
        assert get_all_tools("nonexistent") == []

    def test_fish_mince_tools(self):
        """Fish mince needs only a knife."""
        tools = get_all_tools("fish_mince")
        assert tools == ["knife"]


# ============================================================================
# Validation
# ============================================================================


class TestValidation:
    def test_duplicate_ingredient_id_raises(self, monkeypatch):
        from web import recipes

        original = recipes.INGREDIENTS
        try:
            recipes.INGREDIENTS = [
                {"id": "dup", "name": "A", "type": "store"},
                {"id": "dup", "name": "B", "type": "store"},
            ]
            recipes.RECIPES = []
            recipes._initialize_caches()
            with pytest.raises(RecipeValidationError, match="Duplicate ingredient"):
                validate_recipes()
        finally:
            recipes.INGREDIENTS = original
            recipes.RECIPES = RECIPES
            recipes._initialize_caches()

    def test_duplicate_recipe_id_raises(self):
        from web import recipes

        original_recipes = recipes.RECIPES
        original_ings = recipes.INGREDIENTS
        try:
            recipes.INGREDIENTS = [
                {"id": "flour", "name": "Мука", "type": "store"},
                {"id": "fire", "name": "Огонь", "type": "tool"},
            ]
            recipes.RECIPES = [
                {"id": "dup", "name": "A", "ingredients": ["flour"], "tools": ["fire"]},
                {"id": "dup", "name": "B", "ingredients": ["flour"], "tools": ["fire"]},
            ]
            recipes._initialize_caches()
            with pytest.raises(RecipeValidationError, match="Duplicate recipe"):
                validate_recipes()
        finally:
            recipes.INGREDIENTS = original_ings
            recipes.RECIPES = original_recipes
            recipes._initialize_caches()

    def test_unknown_ref_raises(self):
        from web import recipes

        original_recipes = recipes.RECIPES
        original_ings = recipes.INGREDIENTS
        try:
            recipes.INGREDIENTS = [{"id": "fire", "name": "Огонь", "type": "tool"}]
            recipes.RECIPES = [
                {
                    "id": "bad",
                    "name": "Bad",
                    "ingredients": ["missing_ref"],
                    "tools": ["fire"],
                },
            ]
            recipes._initialize_caches()
            with pytest.raises(RecipeValidationError, match="unknown ingredient"):
                validate_recipes()
        finally:
            recipes.INGREDIENTS = original_ings
            recipes.RECIPES = original_recipes
            recipes._initialize_caches()

    def test_non_tool_used_as_tool_raises(self):
        from web import recipes

        original_recipes = recipes.RECIPES
        original_ings = recipes.INGREDIENTS
        try:
            recipes.INGREDIENTS = [
                {"id": "flour", "name": "Мука", "type": "store"},
            ]
            recipes.RECIPES = [
                {"id": "bad", "name": "Bad", "ingredients": ["flour"], "tools": ["flour"]},
            ]
            recipes._initialize_caches()
            with pytest.raises(RecipeValidationError, match="as tool"):
                validate_recipes()
        finally:
            recipes.INGREDIENTS = original_ings
            recipes.RECIPES = original_recipes
            recipes._initialize_caches()

    def test_cycle_detection_raises(self):
        from web import recipes

        original_recipes = recipes.RECIPES
        original_ings = recipes.INGREDIENTS
        try:
            recipes.INGREDIENTS = [{"id": "fire", "name": "Огонь", "type": "tool"}]
            recipes.RECIPES = [
                {"id": "a", "name": "A", "ingredients": ["b"], "tools": ["fire"]},
                {"id": "b", "name": "B", "ingredients": ["a"], "tools": ["fire"]},
            ]
            recipes._initialize_caches()
            with pytest.raises(RecipeValidationError, match="Circular"):
                validate_recipes()
        finally:
            recipes.INGREDIENTS = original_ings
            recipes.RECIPES = original_recipes
            recipes._initialize_caches()

    def test_id_collision_between_ingredient_and_recipe_raises(self):
        from web import recipes

        original_recipes = recipes.RECIPES
        original_ings = recipes.INGREDIENTS
        try:
            recipes.INGREDIENTS = [
                {"id": "same", "name": "Ing", "type": "store"},
                {"id": "fire", "name": "Огонь", "type": "tool"},
            ]
            recipes.RECIPES = [
                {"id": "same", "name": "Rec", "ingredients": ["fire"], "tools": []},
            ]
            recipes._initialize_caches()
            with pytest.raises(RecipeValidationError, match="both ingredient and recipe"):
                validate_recipes()
        finally:
            recipes.INGREDIENTS = original_ings
            recipes.RECIPES = original_recipes
            recipes._initialize_caches()
