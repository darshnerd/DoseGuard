from rapidfuzz import process
from sqlmodel import Session, select

from app.models import DrugAlias, DrugConcept, MedicineProduct, ProductIngredient
from app.normalize import normalize
from app.services.rxnorm import RxNormClient


class Resolved:
    def __init__(self, ingredient: str, confidence: float, source: str):
        self.ingredient = ingredient
        self.confidence = confidence
        self.source = source


async def resolve_term(session: Session, text_in: str) -> list[Resolved]:
    n = normalize(text_in)
    if not n:
        return []

    prod = session.exec(select(MedicineProduct).where(MedicineProduct.name_normalized == n)).first()
    if prod:
        rows = session.exec(
            select(ProductIngredient).where(ProductIngredient.product_id == prod.id)
        ).all()
        if rows:
            return [Resolved(r.ingredient_normalized, 1.0, "product") for r in rows]

    alias = session.exec(select(DrugAlias).where(DrugAlias.alias_normalized == n)).first()
    if alias:
        return [Resolved(alias.concept_normalized, 0.95, "alias")]
    if session.exec(select(DrugConcept).where(DrugConcept.normalized_name == n)).first():
        return [Resolved(n, 1.0, "concept")]

    names = session.exec(select(DrugConcept.normalized_name)).all()
    m = process.extractOne(n, names, score_cutoff=88)
    if m:
        return [Resolved(m[0], m[1] / 100, "fuzzy")]

    r = await RxNormClient().resolve(text_in)
    if r.matched and r.ingredient_name:
        return [Resolved(normalize(r.ingredient_name), 0.7, "rxnorm")]
    return [Resolved(n, 0.2, "unknown")]


async def resolve_terms(session: Session, texts: list[str]) -> list[Resolved]:
    out, seen = [], set()
    for t in texts:
        for res in await resolve_term(session, t):
            if res.ingredient not in seen:
                seen.add(res.ingredient)
                out.append(res)
    return out
