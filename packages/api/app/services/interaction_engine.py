from itertools import combinations

from sqlmodel import Session, select

from app.models import Interaction

RANK = {"contraindicated": 0, "severe": 1, "moderate": 2, "low": 3}


def check(session: Session, ingredients: list[str]) -> list[dict]:
    norm = sorted({i for i in ingredients if i})
    results = []
    for a, b in combinations(norm, 2):
        a, b = sorted((a, b))
        rows = session.exec(
            select(Interaction).where(Interaction.a_norm == a, Interaction.b_norm == b)
        ).all()
        if not rows:
            continue
        rows.sort(key=lambda r: RANK.get(r.severity, 9))
        top = rows[0]
        results.append({
            "ingredient_a": a, "ingredient_b": b,
            "severity": top.severity,
            "description": next((r.description for r in rows if r.description), None),
            "mechanism": next((r.mechanism for r in rows if r.mechanism), None),
            "source": top.sources,
        })
    results.sort(key=lambda r: RANK.get(r["severity"], 9))
    return results
    