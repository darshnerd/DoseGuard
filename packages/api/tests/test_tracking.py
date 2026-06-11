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
    now = datetime(2026, 6, 8, 18, 0, tzinfo=UTC)
    started = now.date() - timedelta(days=1)

    morning = Medication(user_id=user.id, name="Metformin", start_date=started)
    night = Medication(user_id=user.id, name="Warfarin", start_date=started)
    afternoon = Medication(user_id=user.id, name="Lisinopril", start_date=started)
    session.add_all([morning, night, afternoon])
    session.commit()
    for m in (morning, night, afternoon):
        session.refresh(m)

    session.add_all([
        DoseSchedule(user_id=user.id, medication_id=morning.id, slot="morning"),
        DoseSchedule(user_id=user.id, medication_id=night.id, slot="night"),
        DoseSchedule(user_id=user.id, medication_id=afternoon.id, slot="afternoon"),
    ])
    session.add(
        DoseLog(user_id=user.id, medication_id=morning.id, slot="morning", status="taken", taken_at=now)
    )
    session.commit()

    by_slot = {s.slot: s for s in build_today(session, user, now).slots}
    assert by_slot["morning"].items[0].status == "taken"
    assert by_slot["afternoon"].items[0].status == "overdue"
    assert by_slot["night"].items[0].status == "upcoming"


def test_compute_adherence_active_days():
    session = memory_session()
    user = seed_user(session)
    now = datetime(2026, 6, 8, 12, 0, tzinfo=UTC)

    med = Medication(user_id=user.id, name="Metformin", start_date=now.date() - timedelta(days=30))
    session.add(med)
    session.commit()
    session.refresh(med)
    session.add_all([
        DoseSchedule(user_id=user.id, medication_id=med.id, slot="morning"),
        DoseSchedule(user_id=user.id, medication_id=med.id, slot="night"),
    ])
    session.add(
        DoseLog(user_id=user.id, medication_id=med.id, slot="morning", status="taken", taken_at=now)
    )
    session.commit()

    result = compute_adherence(session, user, days=7, now=now)
    assert result.expected == 14
    assert result.taken == 1
    assert result.percent == round(1 / 14 * 100)


def test_short_course_caps_expected():
    session = memory_session()
    user = seed_user(session)
    now = datetime(2026, 6, 8, 12, 0, tzinfo=UTC)

    med = Medication(
        user_id=user.id,
        name="Amoxicillin",
        start_date=now.date() - timedelta(days=5),
        duration_days=3,
    )
    session.add(med)
    session.commit()
    session.refresh(med)
    session.add(DoseSchedule(user_id=user.id, medication_id=med.id, slot="morning"))
    session.commit()

    result = compute_adherence(session, user, days=7, now=now)
    assert result.expected == 3    # 3 active days, NOT 7


def test_night_dose_goes_overdue_after_cutoff():
    session = memory_session()
    user = seed_user(session)
    now = datetime(2026, 6, 8, 23, 30, tzinfo=UTC)  # past the night cutoff (23:00)
    started = now.date() - timedelta(days=1)

    med = Medication(user_id=user.id, name="Warfarin", start_date=started)
    session.add(med)
    session.commit()
    session.refresh(med)
    session.add(DoseSchedule(user_id=user.id, medication_id=med.id, slot="night"))
    session.commit()

    by_slot = {s.slot: s for s in build_today(session, user, now).slots}
    assert by_slot["night"].items[0].status == "overdue"


def test_adherence_ignores_unscheduled_logs():
    session = memory_session()
    user = seed_user(session)
    now = datetime(2026, 6, 8, 12, 0, tzinfo=UTC)

    med = Medication(user_id=user.id, name="Metformin", start_date=now.date() - timedelta(days=30))
    session.add(med)
    session.commit()
    session.refresh(med)
    session.add(DoseSchedule(user_id=user.id, medication_id=med.id, slot="morning"))

    session.add_all([
        DoseLog(user_id=user.id, medication_id=med.id, slot="morning", status="taken", taken_at=now),
        DoseLog(user_id=user.id, medication_id=med.id, slot="evening", status="taken", taken_at=now),
    ])
    session.commit()

    result = compute_adherence(session, user, days=7, now=now)
    assert result.expected == 7
    assert result.taken == 1


def test_history_buckets_taken_into_local_day():
    from zoneinfo import ZoneInfo

    from app.services.tracking import daily_history

    session = memory_session()
    user = seed_user(session)
    ist = ZoneInfo("Asia/Kolkata")  # UTC+5:30
    now = datetime(2026, 6, 9, 9, 0, tzinfo=ist)

    med = Medication(user_id=user.id, name="Metformin", start_date=now.date() - timedelta(days=10))
    session.add(med)
    session.commit()
    session.refresh(med)
    session.add(DoseSchedule(user_id=user.id, medication_id=med.id, slot="morning"))

    session.add(
        DoseLog(
            user_id=user.id,
            medication_id=med.id,
            slot="morning",
            status="taken",
            taken_at=datetime(2026, 6, 8, 23, 0, tzinfo=UTC),
        )
    )
    session.commit()

    hist = {d.date: d for d in daily_history(session, user, days=3, now=now)}
    assert hist["2026-06-09"].taken == 1
    assert hist["2026-06-08"].taken == 0