from itertools import combinations

from sqlmodel import select

from app.models import Interaction
from app.normalize import normalize

SEVERITY_ORDER = {"contraindicated": 0, "severe": 1, "moderate": 2, "low": 3}


def check_pairs(session, ingredients):
    norm = sorted({normalize(i) for i in ingredients if i})

    found = []
    for a, b in combinations(norm, 2):
        a, b = sorted((a, b))
        stmt = select(Interaction).where(
            Interaction.a_norm == a, Interaction.b_norm == b
        )
        found.extend(session.exec(stmt).all())

    found.sort(key=lambda i: SEVERITY_ORDER.get(i.severity, 99))
    return found
    