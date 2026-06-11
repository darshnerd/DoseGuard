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


def check_pairs_grouped(session, groups):
    norm_groups = [sorted({normalize(i) for i in g if i}) for g in groups]

    pairs = set()
    for x in range(len(norm_groups)):
        for y in range(x + 1, len(norm_groups)):
            for a in norm_groups[x]:
                for b in norm_groups[y]:
                    if a and b and a != b:
                        pairs.add(tuple(sorted((a, b))))

    found = []
    for a, b in pairs:
        stmt = select(Interaction).where(Interaction.a_norm == a, Interaction.b_norm == b)
        found.extend(session.exec(stmt).all())

    found.sort(key=lambda i: SEVERITY_ORDER.get(i.severity, 99))
    return found
    