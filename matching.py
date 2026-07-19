"""
Core logic for comparing fridge contents against recipes.

A recipe is:
- "makeable"  -> every REQUIRED ingredient is in the fridge (optional ones don't matter)
- "almost"    -> missing a small number of required ingredients (default: 1 or 2)
- "not close" -> missing more than that

Matching is done on normalized ingredient names, so it's quantity-agnostic:
we only check "do you have SOME of this ingredient", not "do you have enough".
"""

from models import Recipe, FridgeItem


def get_fridge_ingredient_ids(fridge_items=None):
    if fridge_items is None:
        fridge_items = FridgeItem.query.all()
    return {item.ingredient_id for item in fridge_items}


def classify_recipe(recipe: Recipe, fridge_ids: set, almost_threshold: int = 2):
    """
    Returns a dict describing how makeable a recipe is right now.
    """
    required = recipe.required_ingredients
    required_ids = {link.ingredient_id for link in required}

    have = required_ids & fridge_ids
    missing_links = [link for link in required if link.ingredient_id not in fridge_ids]
    missing_count = len(missing_links)

    if missing_count == 0:
        status = "makeable"
    elif missing_count <= almost_threshold:
        status = "almost"
    else:
        status = "not_close"

    total_required = len(required_ids) or 1  # avoid div by zero for ingredient-less recipes
    match_ratio = len(have) / total_required

    return {
        "recipe": recipe,
        "status": status,
        "missing": missing_links,
        "missing_count": missing_count,
        "match_ratio": match_ratio,
    }


def rank_recipes(recipes, fridge_items=None, almost_threshold: int = 2):
    """
    Classify + sort recipes: makeable first, then almost (fewest missing first),
    then everything else, each group sorted by best match ratio.
    """
    fridge_ids = get_fridge_ingredient_ids(fridge_items)
    results = [classify_recipe(r, fridge_ids, almost_threshold) for r in recipes]

    status_order = {"makeable": 0, "almost": 1, "not_close": 2}
    results.sort(key=lambda r: (status_order[r["status"]], r["missing_count"], -r["match_ratio"]))
    return results
