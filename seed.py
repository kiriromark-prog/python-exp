"""
Optional: run `python seed.py` to populate the database with a few sample
recipes and some fridge items, so you can see the matching in action right away.
"""
from app import app
from models import db, Ingredient, Recipe, RecipeIngredient, FridgeItem

SAMPLE_RECIPES = [
    {
        "title": "Weeknight Fried Rice",
        "servings": 2,
        "prep_time_minutes": 20,
        "instructions": (
            "Cook rice a day ahead and chill. Scramble eggs in a hot wok, set aside. "
            "Stir-fry garlic and veg, add rice, breaking up clumps. Toss in eggs, "
            "soy sauce, and scallions. Serve hot."
        ),
        "ingredients": [
            ("rice", "2", "cups", False),
            ("eggs", "2", "", False),
            ("garlic", "2", "cloves", False),
            ("soy sauce", "2", "tbsp", False),
            ("scallions", "2", "", True),
            ("frozen peas", "0.5", "cup", True),
        ],
    },
    {
        "title": "Tomato Basil Pasta",
        "servings": 4,
        "prep_time_minutes": 25,
        "instructions": (
            "Boil pasta until al dente. Meanwhile saute garlic in olive oil, add "
            "crushed tomatoes and simmer 15 min. Toss with pasta and torn basil. "
            "Finish with parmesan."
        ),
        "ingredients": [
            ("pasta", "400", "g", False),
            ("canned tomatoes", "1", "can", False),
            ("garlic", "3", "cloves", False),
            ("olive oil", "2", "tbsp", False),
            ("basil", "1", "handful", True),
            ("parmesan", "", "", True),
        ],
    },
    {
        "title": "Classic Omelette",
        "servings": 1,
        "prep_time_minutes": 10,
        "instructions": (
            "Whisk eggs with a splash of milk and season. Melt butter in a pan over "
            "medium heat, pour in eggs. Add cheese if using, fold, and serve."
        ),
        "ingredients": [
            ("eggs", "3", "", False),
            ("butter", "1", "tbsp", False),
            ("milk", "1", "tbsp", True),
            ("cheddar cheese", "0.25", "cup", True),
        ],
    },
]

SAMPLE_FRIDGE = ["eggs", "garlic", "rice", "soy sauce", "butter"]


def run():
    with app.app_context():
        db.create_all()

        for recipe_data in SAMPLE_RECIPES:
            if Recipe.query.filter_by(title=recipe_data["title"]).first():
                continue  # don't duplicate on repeat runs
            recipe = Recipe(
                title=recipe_data["title"],
                servings=recipe_data["servings"],
                prep_time_minutes=recipe_data["prep_time_minutes"],
                instructions=recipe_data["instructions"],
            )
            db.session.add(recipe)
            db.session.flush()

            for name, qty, unit, optional in recipe_data["ingredients"]:
                ingredient = Ingredient.get_or_create(name)
                db.session.add(RecipeIngredient(
                    recipe_id=recipe.id, ingredient_id=ingredient.id,
                    quantity=qty or None, unit=unit or None, optional=optional,
                ))

        for name in SAMPLE_FRIDGE:
            ingredient = Ingredient.get_or_create(name)
            if not FridgeItem.query.filter_by(ingredient_id=ingredient.id).first():
                db.session.add(FridgeItem(ingredient_id=ingredient.id))

        db.session.commit()
        print("Seeded sample recipes and fridge items.")


if __name__ == "__main__":
    run()
