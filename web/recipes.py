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
    # Default
    {"id": "water", "name": "Вода", "type": "default"},
    # Store (pack_size = items per pack; omitted = sold individually)
    {"id": "milk", "name": "Молоко", "type": "store", "pack_size": 10},
    {"id": "flour", "name": "Мука", "type": "store", "pack_size": 10},
    {"id": "egg", "name": "Яйцо", "type": "store", "pack_size": 10},
    {"id": "sugar", "name": "Сахар", "type": "store", "pack_size": 10},
    {"id": "rice", "name": "Рисовая крупа", "type": "store", "pack_size": 10},
    {"id": "meat", "name": "Мясо", "type": "store", "pack_size": 1},
    {"id": "ice", "name": "Лед", "type": "store", "pack_size": 10},
    {"id": "vegetables", "name": "Овощи", "type": "store", "pack_size": 10},
    {"id": "fruits", "name": "Фрукты", "type": "store", "pack_size": 10},
    # Fishing
    {"id": "sterlet", "name": "Стерлядь", "type": "fishing"},
    {"id": "salmon", "name": "Лосось", "type": "fishing"},
    {"id": "sturgeon", "name": "Осетр", "type": "fishing"},
    {"id": "black_carp", "name": "Черный амур", "type": "fishing"},
    {"id": "ray", "name": "Скат", "type": "fishing"},
    {"id": "tuna", "name": "Тунец", "type": "fishing"},
    {"id": "dolly_varden", "name": "Мальма", "type": "fishing"},
    {"id": "fugu", "name": "Фугу", "type": "fishing"},
    {"id": "smelt", "name": "Корюшка", "type": "fishing"},
    {"id": "perch", "name": "Окунь", "type": "fishing"},
    {"id": "eel", "name": "Угорь", "type": "fishing"},
    {"id": "pike", "name": "Щука", "type": "fishing"},
    {
        "id": "any_fish",
        "name": "Любая рыба (кроме Фугу, Лосося, Тунца)",
        "type": "fishing",
    },
]

# =============================================================================
# Recipe Definitions
# =============================================================================

RECIPES: List[Recipe] = [
    # ---- Base preparations (intermediates used by other recipes) ----
    {
        "id": "butter",
        "name": "Масло",
        "ingredients": ["milk"],
        "tools": ["whisk"],
    },
    {
        "id": "minced_meat",
        "name": "Мясной фарш",
        "ingredients": ["meat"],
        "tools": ["knife"],
    },
    {
        "id": "fish_mince",
        "name": "Рыбный фарш",
        "ingredients": ["any_fish"],
        "tools": ["knife"],
    },
    {
        "id": "dough",
        "name": "Тесто",
        "ingredients": ["flour", "water", "egg"],
        "tools": ["whisk"],
    },
    {
        "id": "cheese",
        "name": "Сыр",
        "ingredients": ["milk"],
        "tools": ["whisk", "fire"],
    },
    {
        "id": "bread",
        "name": "Хлеб",
        "ingredients": ["dough"],
        "tools": ["fire"],
    },
    {
        "id": "caramel",
        "name": "Карамель",
        "ingredients": ["sugar"],
        "tools": ["fire"],
    },
    {
        "id": "cooked_rice",
        "name": "Вареный рис",
        "ingredients": ["rice", "water"],
        "tools": ["fire"],
    },
    {
        "id": "steak",
        "name": "Стейк",
        "ingredients": ["meat"],
        "tools": ["fire"],
    },
    {
        "id": "broth",
        "name": "Бульон",
        "ingredients": ["meat", "water"],
        "tools": ["fire"],
    },
    {
        "id": "pasta",
        "name": "Макароны",
        "ingredients": ["dough", "water"],
        "tools": ["fire", "knife"],
    },
    {
        "id": "mashed_potatoes",
        "name": "Картофельное пюре",
        "ingredients": ["vegetables", "milk", "butter"],
        "tools": ["whisk", "fire"],
    },
    {
        "id": "ice_cream",
        "name": "Мороженое",
        "ingredients": ["egg", "sugar", "milk", "ice"],
        "tools": ["whisk"],
    },
    # ---- Salads ----
    {
        "id": "fruit_salad",
        "name": "Фруктовый салат",
        "ingredients": ["fruits"],
        "tools": ["knife"],
    },
    {
        "id": "vegetable_salad",
        "name": "Овощной салат",
        "ingredients": ["vegetables"],
        "tools": ["knife"],
    },
    {
        "id": "caprese_salad",
        "name": "Салат Капрезе",
        "ingredients": ["vegetables", "cheese"],
        "tools": ["knife"],
    },
    {
        "id": "olivier_salad",
        "name": "Салат Оливье",
        "ingredients": ["vegetables", "meat", "egg", "water"],
        "tools": ["knife", "fire"],
    },
    # ---- Egg dishes ----
    {
        "id": "fried_eggs",
        "name": "Яичница",
        "ingredients": ["egg"],
        "tools": ["fire"],
    },
    {
        "id": "eggs_and_bacon",
        "name": "Яичница с беконом",
        "ingredients": ["egg", "meat", "butter"],
        "tools": ["fire"],
    },
    {
        "id": "omelette",
        "name": "Омлет",
        "ingredients": ["egg", "milk"],
        "tools": ["whisk", "fire"],
    },
    {
        "id": "vegetable_omelet",
        "name": "Овощной омлет",
        "ingredients": ["egg", "milk", "vegetables"],
        "tools": ["whisk", "fire"],
    },
    {
        "id": "souffle",
        "name": "Суфле",
        "ingredients": ["egg", "sugar"],
        "tools": ["whisk", "fire"],
    },
    {
        "id": "creme_brulee",
        "name": "Крем-брюле",
        "ingredients": ["egg", "milk", "sugar"],
        "tools": ["fire"],
    },
    # ---- Soups & stews ----
    {
        "id": "vegetable_soup",
        "name": "Овощной суп",
        "ingredients": ["vegetables", "broth"],
        "tools": ["fire"],
    },
    {
        "id": "borscht",
        "name": "Борщ",
        "ingredients": ["broth", "vegetables", "meat"],
        "tools": ["fire"],
    },
    {
        "id": "stew",
        "name": "Рагу",
        "ingredients": ["meat", "vegetables", "water"],
        "tools": ["fire"],
    },
    # ---- Cutlets & cutlet combos ----
    {
        "id": "dry_meat_cutlet",
        "name": "Сухая мясная котлета",
        "ingredients": ["minced_meat"],
        "tools": ["fire"],
    },
    {
        "id": "meat_cutlet",
        "name": "Мясная котлета",
        "ingredients": ["minced_meat", "butter"],
        "tools": ["fire"],
    },
    {
        "id": "dry_fish_cutlet",
        "name": "Сухая рыбная котлета",
        "ingredients": ["fish_mince"],
        "tools": ["fire"],
    },
    {
        "id": "fish_cutlet",
        "name": "Рыбная котлета",
        "ingredients": ["fish_mince", "butter"],
        "tools": ["fire"],
    },
    {
        "id": "meat_cutlet_with_mashed_potatoes",
        "name": "Мясная котлета с картофельным пюре",
        "ingredients": ["meat_cutlet", "mashed_potatoes"],
        "tools": [],
    },
    {
        "id": "fish_cutlet_with_mashed_potatoes",
        "name": "Рыбная котлета с картофельным пюре",
        "ingredients": ["fish_cutlet", "mashed_potatoes"],
        "tools": [],
    },
    {
        "id": "meat_cutlet_with_rice",
        "name": "Мясная котлета с рисом",
        "ingredients": ["meat_cutlet", "cooked_rice"],
        "tools": [],
    },
    {
        "id": "fish_cutlet_with_rice",
        "name": "Рыбная котлета с рисом",
        "ingredients": ["fish_cutlet", "cooked_rice"],
        "tools": [],
    },
    # ---- Rice dishes ----
    {
        "id": "salmon_roll",
        "name": "Ролл с лососем",
        "ingredients": ["salmon", "cooked_rice"],
        "tools": ["knife"],
    },
    {
        "id": "tuna_roll",
        "name": "Ролл с тунцом",
        "ingredients": ["tuna", "cooked_rice"],
        "tools": ["knife"],
    },
    {
        "id": "vegetable_roll",
        "name": "Ролл с овощами",
        "ingredients": ["vegetables", "cooked_rice"],
        "tools": ["knife"],
    },
    {
        "id": "fish_with_rice",
        "name": "Рыба с рисом",
        "ingredients": ["any_fish", "cooked_rice"],
        "tools": ["fire"],
    },
    {
        "id": "risotto",
        "name": "Ризотто",
        "ingredients": ["rice", "broth", "cheese"],
        "tools": ["fire"],
    },
    {
        "id": "poke_bowl",
        "name": "Поке",
        "ingredients": ["cooked_rice", "salmon", "vegetables", "cheese"],
        "tools": [],
    },
    # ---- Pasta dishes ----
    {
        "id": "pasta_with_cheese",
        "name": "Макароны с сыром",
        "ingredients": ["pasta", "cheese"],
        "tools": ["fire"],
    },
    {
        "id": "pasta_with_meat_cutlet",
        "name": "Макароны с мясной котлетой",
        "ingredients": ["pasta", "meat_cutlet"],
        "tools": [],
    },
    {
        "id": "pasta_with_fish_cutlet",
        "name": "Макароны с рыбной котлетой",
        "ingredients": ["pasta", "fish_cutlet"],
        "tools": [],
    },
    {
        "id": "pasta_bolognese",
        "name": "Паста Болоньезе",
        "ingredients": ["pasta", "minced_meat", "vegetables", "cheese"],
        "tools": ["fire"],
    },
    {
        "id": "pasta_carbonara",
        "name": "Паста Карбонара",
        "ingredients": ["pasta", "egg", "cheese", "meat"],
        "tools": ["fire"],
    },
    {
        "id": "ramen",
        "name": "Рамен",
        "ingredients": ["broth", "pasta", "meat", "egg"],
        "tools": ["fire"],
    },
    # ---- Meat & fish mains ----
    {
        "id": "meat_with_vegetables",
        "name": "Мясо с овощами",
        "ingredients": ["meat", "vegetables"],
        "tools": ["fire"],
    },
    {
        "id": "fish_with_vegetables",
        "name": "Рыба с овощами",
        "ingredients": ["any_fish", "vegetables"],
        "tools": ["fire"],
    },
    {
        "id": "fried_meat_with_vegetables",
        "name": "Жареное мясо с овощами",
        "ingredients": ["meat", "vegetables", "butter"],
        "tools": ["fire"],
    },
    {
        "id": "fried_fish_with_vegetables",
        "name": "Жареная рыба с овощами",
        "ingredients": ["any_fish", "vegetables", "butter"],
        "tools": ["fire"],
    },
    {
        "id": "french_style_baked_meat",
        "name": "Мясо по-французски",
        "ingredients": ["meat", "vegetables", "cheese"],
        "tools": ["fire"],
    },
    {
        "id": "steak_with_rice",
        "name": "Стейк с рисом",
        "ingredients": ["steak", "cooked_rice"],
        "tools": ["fire"],
    },
    {
        "id": "steak_with_salad",
        "name": "Стейк с салатом",
        "ingredients": ["steak", "vegetable_salad"],
        "tools": [],
    },
    {
        "id": "steak_with_pasta",
        "name": "Стейк с макаронами",
        "ingredients": ["steak", "pasta"],
        "tools": [],
    },
    {
        "id": "steak_with_fruit_sauce",
        "name": "Стейк с фруктовым соусом",
        "ingredients": ["meat", "fruits", "sugar"],
        "tools": ["fire"],
    },
    {
        "id": "steak_with_fruit_sauce_and_rice",
        "name": "Стейк с фруктовым соусом и рисом",
        "ingredients": ["steak_with_fruit_sauce", "cooked_rice"],
        "tools": [],
    },
    {
        "id": "steak_with_fruit_sauce_and_mashed_potatoes",
        "name": "Стейк с фруктовым соусом и картофельным пюре",
        "ingredients": ["steak_with_fruit_sauce", "mashed_potatoes"],
        "tools": [],
    },
    {
        "id": "fish_with_fruit_sauce",
        "name": "Рыба с фруктовым соусом",
        "ingredients": ["any_fish", "fruits", "sugar"],
        "tools": ["fire"],
    },
    {
        "id": "fish_with_fruit_sauce_and_rice",
        "name": "Рыба с фруктовым соусом и рисом",
        "ingredients": ["fish_with_fruit_sauce", "cooked_rice"],
        "tools": [],
    },
    {
        "id": "fish_with_fruit_sauce_and_mashed_potatoes",
        "name": "Рыба с фруктовым соусом и картофельным пюре",
        "ingredients": ["fish_with_fruit_sauce", "mashed_potatoes"],
        "tools": [],
    },
    {
        "id": "dolly_varden_in_cream_sauce",
        "name": "Мальма в сливочном соусе",
        "ingredients": ["dolly_varden", "milk", "vegetables"],
        "tools": ["fire"],
    },
    {
        "id": "burger",
        "name": "Бургер",
        "ingredients": ["bread", "meat_cutlet", "vegetables"],
        "tools": [],
    },
    {
        "id": "beef_taco",
        "name": "Тако с мясом",
        "ingredients": ["bread", "minced_meat", "cheese", "vegetables"],
        "tools": ["fire"],
    },
    {
        "id": "fish_taco",
        "name": "Тако с рыбой",
        "ingredients": ["bread", "fish_mince", "cheese", "vegetables"],
        "tools": ["fire"],
    },
    {
        "id": "burrito",
        "name": "Буррито",
        "ingredients": ["bread", "minced_meat", "cheese", "vegetables", "cooked_rice"],
        "tools": ["fire"],
    },
    {
        "id": "cheese_sandwich",
        "name": "Сэндвич с сыром",
        "ingredients": ["bread", "cheese"],
        "tools": ["knife", "fire"],
    },
    {
        "id": "pizza",
        "name": "Пицца",
        "ingredients": ["dough", "meat", "vegetables", "cheese"],
        "tools": ["fire"],
    },
    {
        "id": "pelmeni",
        "name": "Пельмени",
        "ingredients": ["minced_meat", "dough", "water"],
        "tools": ["fire"],
    },
    {
        "id": "lasagna",
        "name": "Лазанья",
        "ingredients": ["milk", "flour", "minced_meat", "vegetables", "cheese"],
        "tools": ["fire"],
    },
    # ---- Sashimi ----
    {
        "id": "fugu_sashimi",
        "name": "Сашими из Фугу",
        "ingredients": ["fugu"],
        "tools": ["knife"],
    },
    {
        "id": "salmon_sashimi",
        "name": "Сашими из Лосося",
        "ingredients": ["salmon"],
        "tools": ["knife"],
    },
    {
        "id": "tuna_sashimi",
        "name": "Сашими из Тунца",
        "ingredients": ["tuna"],
        "tools": ["knife"],
    },
    # ---- Desserts ----
    {
        "id": "pancakes",
        "name": "Оладьи",
        "ingredients": ["flour", "milk", "egg", "sugar"],
        "tools": ["whisk", "fire"],
    },
    {
        "id": "pancakes_with_caramel",
        "name": "Оладьи с карамелью",
        "ingredients": ["pancakes", "caramel"],
        "tools": [],
    },
    {
        "id": "cheesecake",
        "name": "Чизкейк",
        "ingredients": ["dough", "cheese", "sugar"],
        "tools": ["fire", "whisk"],
    },
    {
        "id": "caramel_cheesecake",
        "name": "Карамельный чизкейк",
        "ingredients": ["cheesecake", "caramel"],
        "tools": [],
    },
    {
        "id": "fruit_cheesecake",
        "name": "Фруктовый чизкейк",
        "ingredients": ["cheesecake", "fruits"],
        "tools": [],
    },
    {
        "id": "caramel_apple",
        "name": "Яблоко в карамели",
        "ingredients": ["fruits", "caramel"],
        "tools": [],
    },
    {
        "id": "fruit_salad_with_caramel",
        "name": "Фруктовый салат с карамелью",
        "ingredients": ["fruit_salad", "caramel"],
        "tools": [],
    },
    {
        "id": "caramel_ice_cream",
        "name": "Карамельное мороженое",
        "ingredients": ["ice_cream", "caramel"],
        "tools": [],
    },
    # ---- Drinks & frozen ----
    {
        "id": "vegetable_smoothie",
        "name": "Овощной смузи",
        "ingredients": ["vegetables", "water"],
        "tools": ["whisk"],
    },
    {
        "id": "fruit_smoothie",
        "name": "Фруктовый смузи",
        "ingredients": ["fruits", "water"],
        "tools": ["whisk"],
    },
    {
        "id": "fruit_popsicle",
        "name": "Фруктовый лед",
        "ingredients": ["fruits", "ice", "sugar"],
        "tools": ["whisk"],
    },
    {
        "id": "compote",
        "name": "Компот",
        "ingredients": ["fruits", "sugar", "water"],
        "tools": ["fire"],
    },
    {
        "id": "milkshake",
        "name": "Молочный коктейль",
        "ingredients": ["ice_cream", "milk"],
        "tools": ["whisk"],
    },
    {
        "id": "caramel_milkshake",
        "name": "Карамельный молочный коктейль",
        "ingredients": ["milkshake", "caramel"],
        "tools": [],
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
