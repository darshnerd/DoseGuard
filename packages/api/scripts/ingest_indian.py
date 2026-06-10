import csv

from _common import SOURCES, normalize


def products():
    with open(SOURCES / "indian.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            name = (r.get("name") or "").strip()
            if not name:
                continue
            ingredients = []
            for col in ("short_composition1", "short_composition2"):
                ing = normalize(r.get(col) or "")
                if ing:
                    ingredients.append(ing)
            yield name, (r.get("manufacturer_name") or "").strip() or None, ingredients
