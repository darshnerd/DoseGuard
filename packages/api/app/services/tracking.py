from datetime import UTC, date, datetime, timedelta

from sqlmodel import select

from app.models import DoseLog, DoseSchedule, Medication, MedicationIngredient
from app.schemas.tracking import AdherenceOut, DayStat, TodayItem, TodayResponse, TodaySlot
from app.services.interactions import check_pairs_grouped

SLOT_ORDER = ["morning", "afternoon", "evening", "night"]
SLOT_CUTOFF = {"morning": 11, "afternoon": 16, "evening": 21, "night": 23}


def is_valid_slot(slot: str) -> bool:
    return slot in SLOT_CUTOFF


def _course_end(med: Medication) -> date | None:
    if med.duration_days is None:
        return None
    return med.start_date + timedelta(days=med.duration_days - 1)


def active_on(med: Medication, day: date) -> bool:
    if day < med.start_date:
        return False
    end = _course_end(med)
    return end is None or day <= end


def _local_date(dt: datetime, ref: datetime) -> date:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(ref.tzinfo or UTC).date()


def _day_window(now: datetime) -> tuple[datetime, datetime]:
    """[start, end) of `now`'s local day, expressed in UTC for DB comparison."""
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)


def _window_bounds(now: datetime, window: list[date]) -> tuple[datetime, datetime]:
    tz = now.tzinfo or UTC
    start = datetime.combine(window[0], datetime.min.time(), tzinfo=tz)
    end = datetime.combine(window[-1] + timedelta(days=1), datetime.min.time(), tzinfo=tz)
    return start.astimezone(UTC), end.astimezone(UTC)


def _expected_keys(schedules, meds, window) -> set[tuple[int, str, date]]:
    keys: set[tuple[int, str, date]] = set()
    for s in schedules:
        med = meds.get(s.medication_id)
        if not med:
            continue
        for day in window:
            if active_on(med, day):
                keys.add((s.medication_id, s.slot, day))
    return keys


def build_today(session, user, now: datetime) -> TodayResponse:
    today = now.date()
    schedules = session.exec(
        select(DoseSchedule).where(DoseSchedule.user_id == user.id)
    ).all()
    meds = {
        m.id: m
        for m in session.exec(
            select(Medication).where(Medication.user_id == user.id)
        ).all()
    }

    ings_by_med: dict[int, list[str]] = {}
    if meds:
        for r in session.exec(
            select(MedicationIngredient).where(
                MedicationIngredient.medication_id.in_(list(meds.keys()))
            )
        ).all():
            ings_by_med.setdefault(r.medication_id, []).append(r.ingredient)

    day_start, day_end = _day_window(now)
    logs = session.exec(
        select(DoseLog).where(
            DoseLog.user_id == user.id,
            DoseLog.taken_at >= day_start,
            DoseLog.taken_at < day_end,
        )
    ).all()
    log_by_key: dict[tuple[int, str], DoseLog] = {}
    for log in sorted(logs, key=lambda x: x.id or 0):
        log_by_key[(log.medication_id, log.slot)] = log

    slots_out: list[TodaySlot] = []
    for slot in SLOT_ORDER:
        # Only schedules whose med's course is active today appear.
        slot_scheds = [
            s
            for s in schedules
            if s.slot == slot and meds.get(s.medication_id) and active_on(meds[s.medication_id], today)
        ]
        items: list[TodayItem] = []
        for s in slot_scheds:
            med = meds[s.medication_id]
            log = log_by_key.get((s.medication_id, slot))
            if log:
                status = log.status
            elif now.hour >= SLOT_CUTOFF[slot]:
                status = "overdue"
            else:
                status = "upcoming"
            items.append(TodayItem(medication_id=med.id, name=med.name, status=status))

        groups = [ings_by_med.get(s.medication_id, []) for s in slot_scheds]
        warnings = [
            f"{i.a_norm} + {i.b_norm} ({i.severity})"
            for i in check_pairs_grouped(session, groups)
        ]

        slots_out.append(TodaySlot(slot=slot, items=items, warnings=warnings))

    adherence = compute_adherence(session, user, now=now)
    return TodayResponse(
        date=today.isoformat(),
        slots=slots_out,
        adherence=adherence.percent,
    )


def _window_days(now: datetime, days: int) -> list[date]:
    today = now.date()
    return [today - timedelta(days=d) for d in range(days - 1, -1, -1)]


def _taken_keys(session, user, now, window, expected_keys) -> set[tuple[int, str, date]]:
    window_start, window_end = _window_bounds(now, window)
    logs = session.exec(
        select(DoseLog).where(
            DoseLog.user_id == user.id,
            DoseLog.status == "taken",
            DoseLog.taken_at >= window_start,
            DoseLog.taken_at < window_end,
        )
    ).all()
    keys: set[tuple[int, str, date]] = set()
    for log in logs:
        key = (log.medication_id, log.slot, _local_date(log.taken_at, now))
        if key in expected_keys:  # ignore logs for unscheduled slots / removed meds
            keys.add(key)
    return keys


def compute_adherence(session, user, days: int = 7, now: datetime | None = None) -> AdherenceOut:
    now = now or datetime.now(UTC)
    window = _window_days(now, days)
    schedules = session.exec(
        select(DoseSchedule).where(DoseSchedule.user_id == user.id)
    ).all()
    meds = {
        m.id: m
        for m in session.exec(select(Medication).where(Medication.user_id == user.id)).all()
    }

    expected_keys = _expected_keys(schedules, meds, window)
    expected = len(expected_keys)
    if expected == 0:
        return AdherenceOut(percent=0, taken=0, expected=0)

    taken = len(_taken_keys(session, user, now, window, expected_keys))
    percent = round(taken / expected * 100)
    return AdherenceOut(percent=percent, taken=taken, expected=expected)


def daily_history(session, user, days: int = 30, now: datetime | None = None) -> list[DayStat]:
    now = now or datetime.now(UTC)
    window = _window_days(now, days)
    schedules = session.exec(
        select(DoseSchedule).where(DoseSchedule.user_id == user.id)
    ).all()
    meds = {
        m.id: m
        for m in session.exec(select(Medication).where(Medication.user_id == user.id)).all()
    }

    expected_keys = _expected_keys(schedules, meds, window)
    taken_keys = _taken_keys(session, user, now, window, expected_keys)

    expected_by_day: dict[date, int] = {}
    for _, _, day in expected_keys:
        expected_by_day[day] = expected_by_day.get(day, 0) + 1
    taken_by_day: dict[date, int] = {}
    for _, _, day in taken_keys:
        taken_by_day[day] = taken_by_day.get(day, 0) + 1

    return [
        DayStat(
            date=day.isoformat(),
            expected=expected_by_day.get(day, 0),
            taken=taken_by_day.get(day, 0),
        )
        for day in window
    ]
