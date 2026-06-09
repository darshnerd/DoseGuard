from datetime import UTC, datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine

from app.models import DoseLog, DoseSchedule, Medication, User
from app.services.tracking import build_today, compute_adherence


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


def test_build_today_statuses():
    session = memory_session()
    user = seed_user(session)

    morning = Medication(user_id=user.id, name="Metformin")
    night = Medication(user_id=user.id, name="Warfarin")
    afternoon = Medication(user_id=user.id, name="Lisinopril")
    session.add_all([morning, night, afternoon])
    session.commit()
    for m in (morning, night, afternoon):
        session.refresh(m)

    session.add_all([
        DoseSchedule(user_id=user.id, medication_id=morning.id, slot="morning"),
        DoseSchedule(user_id=user.id, medication_id=night.id, slot="night"),
        DoseSchedule(user_id=user.id, medication_id=afternoon.id, slot="afternoon"),
    ])

    now = datetime(2026, 6, 8, 18, 0, tzinfo=UTC)
    session.add(
        DoseLog(
            user_id=user.id,
            medication_id=morning.id,
            slot="morning",
            status="taken",
            taken_at=now,
        )
    )
    session.commit()

    today = build_today(session, user, now)
    by_slot = {s.slot: s for s in today.slots}

    assert by_slot["morning"].items[0].status == "taken"
    assert by_slot["afternoon"].items[0].status == "overdue"
    assert by_slot["night"].items[0].status == "upcoming"


def test_compute_adherence_math():
    session = memory_session()
    user = seed_user(session)

    med = Medication(user_id=user.id, name="Metformin")
    session.add(med)
    session.commit()
    session.refresh(med)

    # 2 schedule rows -> expected = 2 * 7 = 14
    session.add_all([
        DoseSchedule(user_id=user.id, medication_id=med.id, slot="morning"),
        DoseSchedule(user_id=user.id, medication_id=med.id, slot="night"),
    ])
    now = datetime(2026, 6, 8, 12, 0, tzinfo=UTC)
    session.add(DoseLog(user_id=user.id, medication_id=med.id, slot="morning", status="taken", taken_at=now))
    session.add(DoseLog(user_id=user.id, medication_id=med.id, slot="morning", status="skipped", taken_at=now))
    session.add(DoseLog(user_id=user.id, medication_id=med.id, slot="night", 
                        status="taken", taken_at=now - timedelta(days=10)))
    session.commit()

    result = compute_adherence(session, user, days=7, now=now)
    assert result.expected == 14
    assert result.taken == 1
    assert result.percent == round(1 / 14 * 100)


def test_adherence_zero_without_schedule():
    session = memory_session()
    user = seed_user(session)
    result = compute_adherence(session, user)
    assert result.percent == 0
    assert result.expected == 0
