from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def normalize_name(name: str) -> str:
    """Lowercase + strip so 'Tomato' and 'tomato ' are treated as the same ingredient."""
    return name.strip().lower()


class Ingredient(db.Model):
    __tablename__ = "ingredients"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)

    recipe_links = db.relationship(
        "RecipeIngredient", back_populates="ingredient", cascade="all, delete-orphan"
    )
    fridge_entry = db.relationship(
        "FridgeItem", back_populates="ingredient", uselist=False, cascade="all, delete-orphan"
    )

    @staticmethod
    def get_or_create(name: str) -> "Ingredient":
        normalized = normalize_name(name)
        ingredient = Ingredient.query.filter_by(name=normalized).first()
        if ingredient is None:
            ingredient = Ingredient(name=normalized)
            db.session.add(ingredient)
            db.session.flush()  # get an id without committing yet
        return ingredient

    def __repr__(self):
        return f"<Ingredient {self.name}>"


class Recipe(db.Model):
    __tablename__ = "recipes"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    instructions = db.Column(db.Text, nullable=False, default="")
    servings = db.Column(db.Integer)
    prep_time_minutes = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ingredient_links = db.relationship(
        "RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan",
        order_by="RecipeIngredient.id"
    )

    @property
    def required_ingredients(self):
        return [link for link in self.ingredient_links if not link.optional]

    @property
    def optional_ingredients(self):
        return [link for link in self.ingredient_links if link.optional]

    def __repr__(self):
        return f"<Recipe {self.title}>"


class RecipeIngredient(db.Model):
    """Association object between Recipe and Ingredient, carrying quantity/unit/optional."""
    __tablename__ = "recipe_ingredients"

    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"), nullable=False)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False)
    quantity = db.Column(db.String(50))  # free-text: "2", "1.5", "a pinch"
    unit = db.Column(db.String(30))      # e.g. "cups", "g", "tbsp"
    optional = db.Column(db.Boolean, default=False, nullable=False)

    recipe = db.relationship("Recipe", back_populates="ingredient_links")
    ingredient = db.relationship("Ingredient", back_populates="recipe_links")

    @property
    def display_amount(self):
        parts = [p for p in [self.quantity, self.unit] if p]
        return " ".join(parts)


class FridgeItem(db.Model):
    """What the user currently has on hand. One row per ingredient."""
    __tablename__ = "fridge_items"

    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), unique=True, nullable=False)
    quantity = db.Column(db.String(50))  # optional free-text amount on hand
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    ingredient = db.relationship("Ingredient", back_populates="fridge_entry")
