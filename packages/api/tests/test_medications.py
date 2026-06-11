import httpx
import pytest
import respx
from httpx import Response
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import DoseLog, DoseSchedule, Medication, MedicationIngredient, User
from app.routers.medications import add_medication, delete_medication
from app.schemas.medication import MedicationCreate

BASE = "https://rxnav.nlm.nih.gov/REST"


def memory_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def seed_user(session):
    user = User(email="a@b.com", hashed_password="x")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_delete_medication_removes_dose_logs():
    session = memory_session()
    user = seed_user(session)
    med = Medication(user_id=user.id, name="Metformin")
    session.add(med)
    session.commit()
    session.refresh(med)
    session.add_all([
        MedicationIngredient(medication_id=med.id, ingredient="metformin"),
        DoseSchedule(user_id=user.id, medication_id=med.id, slot="morning"),
        DoseLog(user_id=user.id, medication_id=med.id, slot="morning", status="taken"),
    ])
    session.commit()

    delete_medication(med.id, user, session)

    assert session.exec(select(DoseLog).where(DoseLog.medication_id == med.id)).all() == []
    assert session.exec(select(DoseSchedule).where(DoseSchedule.medication_id == med.id)).all() == []
    assert session.get(Medication, med.id) is None


@respx.mock
async def test_add_medication_no_partial_write_on_resolve_failure():
    session = memory_session()
    user = seed_user(session)
    respx.get(f"{BASE}/approximateTerm.json").mock(return_value=Response(503))

    req = MedicationCreate(name="Warfarin", duration_days=5)
    with pytest.raises(httpx.HTTPStatusError):
        await add_medication(req, user, session)

    assert session.exec(select(Medication).where(Medication.user_id == user.id)).all() == []
    assert session.exec(select(MedicationIngredient)).all() == []
