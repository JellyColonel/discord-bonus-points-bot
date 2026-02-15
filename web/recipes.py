"""
Recipe definitions, ingredient lookups, and dependency resolution.

Recipes model the GTA 5 RP cooking mechanic: combine store-bought ingredients
with kitchen tools to create dishes. Recipe outputs can be inputs for other
recipes (chaining). All quantities are 1 per ingredient per step.
"""

from typing import Any, Dict, List, Optional, Set

# Type aliases
Ingredient = Dict[str, str]
Recipe = Dict[str, Any]

# =============================================================================
# Ingredient Definitions
# =============================================================================
# Types:
#   "tool"    — kitchen tools (reusable, not consumed)
#   "store"   — purchased from a store (optional "pack_size" for bulk packs)
#   "default" — freely available (e.g. water)
#   "fishing" — caught by fishing

INGREDIENTS: List[Ingredient] = [
    # Tools
    {"id": "knife", "name": "Нож", "type": "tool"},
    {"id": "whisk", "name": "Венчик", "type": "tool"},
    {"id": "fire", "name": "Огонь", "type": "tool"},
    {"id": "blender", "name": "Блендер", "type": "tool"},
    {"id": "juicer", "name": "Соковыжималка", "type": "tool"},
    # Default
    {"id": "water", "name": "Вода", "type": "default"},
    # Store (pack_size = items per pack; omitted = sold individually)
    {"id": "milk", "name": "Молоко", "type": "store"},
    {"id": "flour", "name": "Мука", "type": "store", "pack_size": 10},
    {"id": "egg", "name": "Яйцо", "type": "store", "pack_size": 10},
    {"id": "sugar", "name": "Сахар", "type": "store"},
    {"id": "salt", "name": "Соль", "type": "store"},
    {"id": "butter", "name": "Сливочное масло", "type": "store"},
    {"id": "cheese", "name": "Сыр", "type": "store"},
    {"id": "tomato", "name": "Помидор", "type": "store", "pack_size": 10},
    {"id": "onion", "name": "Лук", "type": "store", "pack_size": 10},
    {"id": "garlic", "name": "Чеснок", "type": "store", "pack_size": 10},
    {"id": "pepper", "name": "Перец", "type": "store", "pack_size": 10},
    {"id": "rice", "name": "Рис", "type": "store"},
    {"id": "chicken", "name": "Курица", "type": "store"},
    {"id": "beef", "name": "Говядина", "type": "store"},
    {"id": "cream", "name": "Сливки", "type": "store"},
    {"id": "lemon", "name": "Лимон", "type": "store", "pack_size": 10},
    {"id": "apple", "name": "Яблоко", "type": "store", "pack_size": 10},
    {"id": "cocoa", "name": "Какао", "type": "store"},
    {"id": "yeast", "name": "Дрожжи", "type": "store"},
    {"id": "sausage", "name": "Колбаса", "type": "store"},
    # Fishing
    {"id": "sterlet", "name": "Стерлядь", "type": "fishing"},
    {"id": "salmon", "name": "Лосось", "type": "fishing"},
    {"id": "sturgeon", "name": "Осётр", "type": "fishing"},
    {"id": "black_carp", "name": "Чёрный амур", "type": "fishing"},
    {"id": "ray", "name": "Скат", "type": "fishing"},
    {"id": "tuna", "name": "Тунец", "type": "fishing"},
    {"id": "dolly_varden", "name": "Мальма", "type": "fishing"},
    {"id": "fugu", "name": "Фугу", "type": "fishing"},
    {"id": "smelt", "name": "Корюшка", "type": "fishing"},
    {"id": "perch", "name": "Окунь", "type": "fishing"},
    {"id": "eel", "name": "Угорь", "type": "fishing"},
    {"id": "pike", "name": "Щука", "type": "fishing"},
    {"id": "any_fish", "name": "Любая рыба (кроме Фугу, Лосося, Тунца)", "type": "fishing"},
]

# =============================================================================
# Recipe Definitions
# =============================================================================

RECIPES: List[Recipe] = [
    # --- Simple recipes (no sub-recipes) ---
    {
        "id": "scrambled_eggs",
        "name": "Яичница",
        "ingredients": ["egg", "salt", "butter"],
        "tools": ["fire"],
    },
    {
        "id": "salad",
        "name": "Салат",
        "ingredients": ["tomato", "onion", "salt"],
        "tools": ["knife"],
    },
    {
        "id": "lemonade",
        "name": "Лимонад",
        "ingredients": ["lemon", "sugar", "water"],
        "tools": ["juicer"],
    },
    # --- Multi-step recipes ---
    {
        "id": "dough",
        "name": "Тесто",
        "ingredients": ["flour", "water", "egg"],
        "tools": ["whisk"],
    },
    {
        "id": "macaroni",
        "name": "Макароны",
        "ingredients": ["dough", "water"],
        "tools": ["knife", "fire"],
    },
    {
        "id": "mac_and_cheese",
        "name": "Макароны с сыром",
        "ingredients": ["macaroni", "cheese", "butter"],
        "tools": ["fire"],
    },
    {
        "id": "tomato_sauce",
        "name": "Томатный соус",
        "ingredients": ["tomato", "garlic", "onion", "salt"],
        "tools": ["knife", "fire"],
    },
    {
        "id": "pasta_with_sauce",
        "name": "Паста с соусом",
        "ingredients": ["macaroni", "tomato_sauce"],
        "tools": ["fire"],
    },
    {
        "id": "pizza_dough",
        "name": "Тесто для пиццы",
        "ingredients": ["dough", "yeast", "salt"],
        "tools": ["whisk"],
    },
    {
        "id": "pizza",
        "name": "Пицца",
        "ingredients": ["pizza_dough", "tomato_sauce", "cheese", "sausage"],
        "tools": ["fire"],
    },
    {
        "id": "fish_mince",
        "name": "Рыбный фарш",
        "ingredients": ["any_fish"],
        "tools": ["knife"],
    },
]

# =============================================================================
# Caching and Lookup Functions
# =============================================================================

_INGREDIENTS_BY_ID: Dict[str, Ingredient] = {}
_RECIPES_BY_ID: Dict[str, Recipe] = {}


def _initialize_caches() -> None:
    """Initialize lookup dictionaries from definition lists."""
    global _INGREDIENTS_BY_ID, _RECIPES_BY_ID
    _INGREDIENTS_BY_ID = {ing["id"]: ing for ing in INGREDIENTS}
    _RECIPES_BY_ID = {rec["id"]: rec for rec in RECIPES}


_initialize_caches()

TOTAL_RECIPES = len(RECIPES)


def get_all_recipes() -> List[Recipe]:
    """Get list of all recipes."""
    return RECIPES


def get_all_ingredients() -> List[Ingredient]:
    """Get list of all ingredients."""
    return INGREDIENTS


def get_recipe_by_id(recipe_id: str) -> Optional[Recipe]:
    """Find recipe by ID. O(1) dictionary lookup."""
    return _RECIPES_BY_ID.get(recipe_id)


def get_ingredient_by_id(ingredient_id: str) -> Optional[Ingredient]:
    """Find ingredient by ID. O(1) dictionary lookup."""
    return _INGREDIENTS_BY_ID.get(ingredient_id)


def is_recipe(ref_id: str) -> bool:
    """Check if an ID refers to a recipe (vs a base ingredient)."""
    return ref_id in _RECIPES_BY_ID


def resolve_name(ref_id: str) -> str:
    """Get display name for an ingredient or recipe ID."""
    if ref_id in _RECIPES_BY_ID:
        return _RECIPES_BY_ID[ref_id]["name"]
    if ref_id in _INGREDIENTS_BY_ID:
        return _INGREDIENTS_BY_ID[ref_id]["name"]
    return ref_id


# =============================================================================
# Dependency Resolution
# =============================================================================


def get_sub_recipes(recipe_id: str) -> List[Recipe]:
    """Get ordered list of sub-recipe steps needed to make this recipe.

    Returns sub-recipes in topological order (dependencies first).
    Does NOT include the recipe itself.
    """
    result: List[Recipe] = []
    visited: Set[str] = set()

    def _collect(rid: str) -> None:
        recipe = _RECIPES_BY_ID.get(rid)
        if not recipe:
            return
        for ing_id in recipe["ingredients"]:
            if ing_id in _RECIPES_BY_ID and ing_id not in visited:
                visited.add(ing_id)
                _collect(ing_id)
                result.append(_RECIPES_BY_ID[ing_id])

    _collect(recipe_id)
    return result


def get_shopping_list(recipe_id: str) -> Dict[str, int]:
    """Recursively collect all purchasable ingredients needed for a recipe.

    Collects store-type and fishing-type ingredients. Returns a dict of
    {ingredient_id: count}. Each appearance of an ingredient in any sub-recipe
    or the recipe itself counts as 1. Shared sub-recipes are only counted once
    (deduplicated via visited set).
    """
    counts: Dict[str, int] = {}
    visited: Set[str] = set()

    def _collect(rid: str) -> None:
        if rid in visited:
            return
        visited.add(rid)
        recipe = _RECIPES_BY_ID.get(rid)
        if not recipe:
            return
        for ing_id in recipe["ingredients"]:
            if ing_id in _RECIPES_BY_ID:
                _collect(ing_id)
            elif ing_id in _INGREDIENTS_BY_ID:
                ing = _INGREDIENTS_BY_ID[ing_id]
                if ing["type"] in ("store", "fishing"):
                    counts[ing_id] = counts.get(ing_id, 0) + 1

    _collect(recipe_id)
    return counts


def get_all_tools(recipe_id: str) -> List[str]:
    """Get union of all tool IDs needed across a recipe and its sub-recipes.

    Returns tool IDs in a stable order (order of first encounter).
    """
    tools: List[str] = []
    seen: Set[str] = set()

    def _collect(rid: str) -> None:
        recipe = _RECIPES_BY_ID.get(rid)
        if not recipe:
            return
        # Recurse into sub-recipes first
        for ing_id in recipe["ingredients"]:
            if ing_id in _RECIPES_BY_ID:
                _collect(ing_id)
        # Then add this recipe's tools
        for tool_id in recipe.get("tools", []):
            if tool_id not in seen:
                seen.add(tool_id)
                tools.append(tool_id)

    _collect(recipe_id)
    return tools


# =============================================================================
# Validation (runs at module load)
# =============================================================================


class RecipeValidationError(Exception):
    """Raised when recipe data integrity checks fail."""


def validate_recipes() -> None:
    """Validate recipe data integrity.

    Checks:
    - No duplicate ingredient IDs
    - No duplicate recipe IDs
    - All ingredient refs in recipes resolve to a known ingredient or recipe
    - All tool refs resolve to a known tool-type ingredient
    - No circular dependencies between recipes
    """
    # Check duplicate ingredient IDs
    ing_ids = [ing["id"] for ing in INGREDIENTS]
    dupes = [x for x in ing_ids if ing_ids.count(x) > 1]
    if dupes:
        raise RecipeValidationError(f"Duplicate ingredient IDs: {set(dupes)}")

    # Check duplicate recipe IDs
    rec_ids = [rec["id"] for rec in RECIPES]
    dupes = [x for x in rec_ids if rec_ids.count(x) > 1]
    if dupes:
        raise RecipeValidationError(f"Duplicate recipe IDs: {set(dupes)}")

    # Check ID collisions between ingredients and recipes
    collisions = set(ing_ids) & set(rec_ids)
    if collisions:
        raise RecipeValidationError(f"IDs used as both ingredient and recipe: {collisions}")

    # Check ingredient types
    valid_types = {"tool", "store", "default", "fishing"}
    for ing in INGREDIENTS:
        if ing["type"] not in valid_types:
            raise RecipeValidationError(
                f"Ingredient '{ing['id']}' has invalid type '{ing['type']}'"
            )

    # Check all refs resolve
    valid_ids = set(ing_ids) | set(rec_ids)
    for recipe in RECIPES:
        for ing_id in recipe["ingredients"]:
            if ing_id not in valid_ids:
                raise RecipeValidationError(
                    f"Recipe '{recipe['id']}' references unknown ingredient '{ing_id}'"
                )
        for tool_id in recipe.get("tools", []):
            if tool_id not in _INGREDIENTS_BY_ID:
                raise RecipeValidationError(
                    f"Recipe '{recipe['id']}' references unknown tool '{tool_id}'"
                )
            if _INGREDIENTS_BY_ID[tool_id]["type"] != "tool":
                raise RecipeValidationError(
                    f"Recipe '{recipe['id']}' uses '{tool_id}' as tool, "
                    f"but it has type '{_INGREDIENTS_BY_ID[tool_id]['type']}'"
                )

    # Check for cycles using DFS
    def _has_cycle(rid: str, path: Set[str]) -> bool:
        recipe = _RECIPES_BY_ID.get(rid)
        if not recipe:
            return False
        for ing_id in recipe["ingredients"]:
            if ing_id in path:
                return True
            if ing_id in _RECIPES_BY_ID:
                if _has_cycle(ing_id, path | {ing_id}):
                    return True
        return False

    for recipe in RECIPES:
        if _has_cycle(recipe["id"], {recipe["id"]}):
            raise RecipeValidationError(
                f"Circular dependency detected involving recipe '{recipe['id']}'"
            )


# Run validation at import time
validate_recipes()
