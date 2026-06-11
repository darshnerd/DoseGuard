from sqlmodel import Session, SQLModel, create_engine

from app.models import Interaction
from app.services.interactions import check_pairs


def memory_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_finds_conflict_any_case_or_order():
    session = memory_session()
    session.add(
        Interaction(
            a_norm="aspirin",
            b_norm="warfarin",
            severity="severe",
            description="bleeding",
        )
    )
    session.commit()

    results = check_pairs(session, ["Warfarin", "ASPIRIN"])
    assert len(results) == 1
    assert results[0].severity == "severe"


def test_no_conflict_returns_empty():
    session = memory_session()
    assert check_pairs(session, ["aspirin", "metformin"]) == []
    