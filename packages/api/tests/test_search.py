from sqlmodel import Session, SQLModel, create_engine

from app.models import DrugConcept, MedicineProduct
from app.services.search import search_drugs


def memory_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_exact_concept_outranks_loose_product_match():
    session = memory_session()
    session.add(DrugConcept(canonical_name="Aspirin", normalized_name="aspirin"))

    session.add(MedicineProduct(name="Aspirin Plus C", name_normalized="aspirin plus c", source="t"))
    session.commit()

    results = search_drugs(session, "aspirin", limit=10)

    assert results[0]["normalized"] == "aspirin"
    assert results[0]["kind"] == "concept"


def test_search_dedupes_products_by_normalized_name():
    session = memory_session()
    session.add(MedicineProduct(name="Crocin", name_normalized="crocin", manufacturer="GSK", source="t"))
    session.add(MedicineProduct(name="Crocin", name_normalized="crocin", manufacturer="Other", source="t"))
    session.commit()

    results = search_drugs(session, "crocin", limit=10)

    assert len([r for r in results if r["normalized"] == "crocin"]) == 1
