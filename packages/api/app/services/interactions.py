from itertools import combinations

from sqlmodel import select

from app.models import Interaction

SEVERITY_ORDER = {"contraindicated": 0, "severe": 1, "moderate": 2, "low": 3}


def check_pairs(session, ingredients):
    norm = sorted({i.lower() for i in ingredients if i})

    found = []
    for a, b in combinations(norm, 2):
        stmt = select(Interaction).where(
            ((Interaction.ingredient_a == a) & (Interaction.ingredient_b == b))
            | ((Interaction.ingredient_a == b) & (Interaction.ingredient_b == a))
        )
        found.extend(session.exec(stmt).all())

    found.sort(key=lambda i: SEVERITY_ORDER.get(i.severity, 99))
    return found
    