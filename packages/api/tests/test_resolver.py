from sqlmodel import Session, SQLModel, create_engine

from app.models import DrugAlias, DrugConcept, MedicineProduct, ProductIngredient
from app.normalize import normalize
from app.services.normalization import resolve_term


def memory_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def seed(session):
    session.add(DrugConcept(canonical_name="Ibuprofen", normalized_name="ibuprofen"))
    session.add(DrugConcept(canonical_name="Warfarin", normalized_name="warfarin"))
    session.add(DrugAlias(alias_normalized="brufen", concept_normalized="ibuprofen", source="test"))
    product = MedicineProduct(name="Combiflam", name_normalized="combiflam", source="test")
    session.add(product)
    session.commit()
    session.refresh(product)
    session.add(ProductIngredient(product_id=product.id, ingredient_normalized="ibuprofen"))
    session.add(ProductIngredient(product_id=product.id, ingredient_normalized=normalize("Paracetamol")))
    session.commit()


def test_normalize_strips_strength_and_aliases():
    assert normalize("Paracetamol 500mg") == "acetaminophen"
    assert normalize("IBUPROFEN (200 MG)") == "ibuprofen"


async def test_resolve_exact_concept():
    session = memory_session()
    seed(session)
    res = await resolve_term(session, "Ibuprofen 400mg")
    assert res[0].ingredient == "ibuprofen"
    assert res[0].confidence == 1.0


async def test_resolve_alias():
    session = memory_session()
    seed(session)
    res = await resolve_term(session, "Brufen")
    assert res[0].ingredient == "ibuprofen"
    assert res[0].source == "alias"


async def test_resolve_product_expands_ingredients():
    session = memory_session()
    seed(session)
    res = await resolve_term(session, "Combiflam")
    assert {r.ingredient for r in res} == {"ibuprofen", "acetaminophen"}
