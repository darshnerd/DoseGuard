from sqlmodel import Session, SQLModel, create_engine

from app.models import Interaction
from app.services.interaction_engine import check


def memory_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def seed(session):
    session.add(Interaction(a_norm="ibuprofen", b_norm="warfarin", severity="severe",
                            description="Increased bleeding risk", sources="Curated"))
    session.add(Interaction(a_norm="aspirin", b_norm="warfarin", severity="moderate",
                            sources="DDInter"))
    session.commit()


def test_check_finds_known_pair():
    session = memory_session()
    seed(session)
    results = check(session, ["warfarin", "ibuprofen", "amoxicillin"])
    assert len(results) == 1
    assert results[0]["severity"] == "severe"
    assert results[0]["ingredient_a"] == "ibuprofen"


def test_check_orders_by_severity():
    session = memory_session()
    seed(session)
    results = check(session, ["warfarin", "ibuprofen", "aspirin"])
    assert [r["severity"] for r in results] == ["severe", "moderate"]


def test_check_no_pairs():
    session = memory_session()
    seed(session)
    assert check(session, ["amoxicillin"]) == []
    