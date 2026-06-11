from rapidfuzz import fuzz, process
from sqlmodel import Session, select

from app.models import DrugConcept, MedicineProduct
from app.normalize import normalize


def search_drugs(session: Session, query: str, limit: int = 10) -> list[dict]:
    n = normalize(query)
    if not n:
        return []

    results: list[dict] = []
    seen: set[str] = set()

    products = session.exec(
        select(MedicineProduct).where(MedicineProduct.name_normalized.contains(n))
    ).all()
    product_count = 0
    for p in products:
        if p.name_normalized in seen:
            continue
        seen.add(p.name_normalized)
        score = 100 if p.name_normalized == n else int(fuzz.WRatio(n, p.name_normalized))
        results.append({
            "name": p.name,
            "normalized": p.name_normalized,
            "kind": "product",
            "manufacturer": p.manufacturer,
            "score": score,
        })
        product_count += 1
        if product_count >= limit:
            break

    concept_names = session.exec(select(DrugConcept.normalized_name)).all()
    for name, score, _ in process.extract(n, concept_names, scorer=fuzz.WRatio, limit=limit):
        if name in seen or score < 70:
            continue
        seen.add(name)
        results.append({
            "name": name,
            "normalized": name,
            "kind": "concept",
            "manufacturer": None,
            "score": int(score),
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]
