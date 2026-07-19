import os

from flask import Flask, render_template, request, redirect, url_for, flash

from models import db, Ingredient, Recipe, RecipeIngredient, FridgeItem, normalize_name
from matching import rank_recipes, get_fridge_ingredient_ids, classify_recipe

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'recipes.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-key-change-me"

    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def register_routes(app):

    @app.route("/")
    def dashboard():
        fridge_items = FridgeItem.query.join(Ingredient).order_by(Ingredient.name).all()
        recipes = Recipe.query.all()
        ranked = rank_recipes(recipes, fridge_items)

        makeable = [r for r in ranked if r["status"] == "makeable"]
        almost = [r for r in ranked if r["status"] == "almost"]

        return render_template(
            "index.html",
            fridge_items=fridge_items,
            makeable=makeable,
            almost=almost,
            total_recipes=len(recipes),
        )

    # ---------- Fridge management ----------

    @app.route("/fridge", methods=["GET", "POST"])
    def fridge():
        if request.method == "POST":
            raw_names = request.form.get("ingredient_names", "")
            quantity = request.form.get("quantity", "").strip()

            # allow comma or newline separated bulk entry
            names = [n for n in raw_names.replace("\n", ",").split(",") if n.strip()]

            added = 0
            for name in names:
                ingredient = Ingredient.get_or_create(name)
                existing = FridgeItem.query.filter_by(ingredient_id=ingredient.id).first()
                if existing:
                    if quantity:
                        existing.quantity = quantity
                else:
                    db.session.add(FridgeItem(ingredient_id=ingredient.id, quantity=quantity or None))
                    added += 1
            db.session.commit()
            flash(f"Added {added} new item(s) to your fridge.", "success")
            return redirect(url_for("fridge"))

        fridge_items = FridgeItem.query.join(Ingredient).order_by(Ingredient.name).all()
        return render_template("fridge.html", fridge_items=fridge_items)

    @app.route("/fridge/<int:item_id>/delete", methods=["POST"])
    def delete_fridge_item(item_id):
        item = FridgeItem.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash("Removed from fridge.", "success")
        return redirect(url_for("fridge"))

    @app.route("/fridge/clear", methods=["POST"])
    def clear_fridge():
        FridgeItem.query.delete()
        db.session.commit()
        flash("Fridge cleared.", "success")
        return redirect(url_for("fridge"))

    # ---------- Recipes ----------

    @app.route("/recipes")
    def list_recipes():
        recipes = Recipe.query.order_by(Recipe.title).all()
        fridge_ids = get_fridge_ingredient_ids()
        classified = [classify_recipe(r, fridge_ids) for r in recipes]
        return render_template("recipes.html", classified=classified)

    @app.route("/recipes/new", methods=["GET", "POST"])
    def new_recipe():
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            instructions = request.form.get("instructions", "").strip()
            servings = request.form.get("servings") or None
            prep_time = request.form.get("prep_time_minutes") or None

            if not title:
                flash("A recipe needs a title.", "error")
                return redirect(url_for("new_recipe"))

            recipe = Recipe(
                title=title,
                instructions=instructions,
                servings=int(servings) if servings else None,
                prep_time_minutes=int(prep_time) if prep_time else None,
            )
            db.session.add(recipe)
            db.session.flush()

            ing_names = request.form.getlist("ingredient_name")
            ing_qty = request.form.getlist("ingredient_quantity")
            ing_unit = request.form.getlist("ingredient_unit")
            ing_optional = request.form.getlist("ingredient_optional")  # list of indices marked optional

            for i, name in enumerate(ing_names):
                if not name.strip():
                    continue
                ingredient = Ingredient.get_or_create(name)
                link = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient.id,
                    quantity=ing_qty[i].strip() if i < len(ing_qty) else None,
                    unit=ing_unit[i].strip() if i < len(ing_unit) else None,
                    optional=str(i) in ing_optional,
                )
                db.session.add(link)

            db.session.commit()
            flash(f"Saved recipe '{recipe.title}'.", "success")
            return redirect(url_for("view_recipe", recipe_id=recipe.id))

        return render_template("recipe_form.html", recipe=None)

    @app.route("/recipes/<int:recipe_id>")
    def view_recipe(recipe_id):
        recipe = Recipe.query.get_or_404(recipe_id)
        fridge_ids = get_fridge_ingredient_ids()
        result = classify_recipe(recipe, fridge_ids)
        return render_template("recipe_detail.html", recipe=recipe, result=result, fridge_ids=fridge_ids)

    @app.route("/recipes/<int:recipe_id>/delete", methods=["POST"])
    def delete_recipe(recipe_id):
        recipe = Recipe.query.get_or_404(recipe_id)
        db.session.delete(recipe)
        db.session.commit()
        flash(f"Deleted '{recipe.title}'.", "success")
        return redirect(url_for("list_recipes"))

    @app.route("/recipes/<int:recipe_id>/add-missing-to-fridge", methods=["POST"])
    def add_missing_to_fridge(recipe_id):
        """Convenience: one click adds every missing required ingredient to the fridge."""
        recipe = Recipe.query.get_or_404(recipe_id)
        fridge_ids = get_fridge_ingredient_ids()
        result = classify_recipe(recipe, fridge_ids)
        for link in result["missing"]:
            db.session.add(FridgeItem(ingredient_id=link.ingredient_id))
        db.session.commit()
        flash("Added missing ingredients to your fridge.", "success")
        return redirect(url_for("view_recipe", recipe_id=recipe_id))


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
