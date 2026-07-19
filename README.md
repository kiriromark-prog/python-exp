# Fridge → Fork

A small Flask + SQLAlchemy app that tracks what's in your fridge and tells you
which of your saved recipes you can actually cook right now.

## How the matching works

- Every recipe is a list of ingredients, each optionally marked **optional**
  (garnishes, swaps, "if you have it" items).
- A recipe is **"Ready to cook"** if every *required* ingredient is in your fridge.
  Optional ingredients don't block this.
- A recipe is **"Almost there"** if it's missing just 1–2 required ingredients
  (configurable in `matching.py` via `almost_threshold`).
- Matching is by ingredient name only (not quantity) — it checks "do you have
  some flour", not "do you have exactly 400g of flour". This keeps the app
  simple and forgiving, since real cooking rarely needs exact amounts.
- Ingredient names are normalized (lowercased/trimmed) so "Garlic" and "garlic "
  are recognized as the same thing. Typos across different names (e.g. "scallion"
  vs "green onion") will still be treated as different ingredients — see
  "Possible improvements" below.

## Setup

```bash
cd recipe_app
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Run it

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

The first run creates `recipes.db` (SQLite) automatically in the project folder.

## Optional: load sample data

To try the app immediately with a few pre-made recipes and a partially-stocked
fridge:

```bash
python seed.py
```

This adds three recipes (fried rice, tomato basil pasta, an omelette) and
stocks the fridge with eggs, garlic, rice, soy sauce, and butter — so you'll
immediately see one recipe ready to cook and others "almost there".

## Project structure

```
recipe_app/
├── app.py            # Flask app + all routes
├── models.py          # SQLAlchemy models (Recipe, Ingredient, FridgeItem, ...)
├── matching.py         # Logic that compares fridge contents to recipes
├── seed.py            # Optional sample-data loader
├── requirements.txt
├── static/style.css
└── templates/
    ├── base.html
    ├── index.html          # "Tonight" dashboard — the main matching view
    ├── fridge.html         # add/remove fridge items
    ├── recipes.html        # full recipe list sorted by readiness
    ├── recipe_form.html    # add a new recipe
    └── recipe_detail.html  # single recipe + ingredient checklist
```

## Data model

- **Ingredient** — a canonical, deduplicated ingredient name.
- **Recipe** — title, instructions, servings, prep time.
- **RecipeIngredient** — join table between Recipe and Ingredient; carries
  quantity, unit, and an `optional` flag.
- **FridgeItem** — one row per ingredient currently on hand, with an optional
  quantity note.

## Possible improvements

- **Fuzzy ingredient matching** — treat "scallion"/"green onion" or
  "cilantro"/"coriander" as equivalent via a synonym table.
- **Quantity-aware matching** — currently a recipe counts an ingredient as
  "have" if you have *any* amount; you could compare against the recipe's
  required quantity.
- **Multi-user support** — right now the fridge is global/single-user; adding
  Flask-Login and a `user_id` foreign key on `FridgeItem` would let multiple
  people use the same instance.
- **Recipe import** — paste a recipe URL or text blob and auto-extract the
  ingredient list.
- **Expiry tracking** — add a `use_by` date to `FridgeItem` and highlight
  recipes that use ingredients about to expire.
