from datetime import UTC, datetime, timedelta

from sqlmodel import select

from app.models import DoseLog, DoseSchedule, Medication, MedicationIngredient
from app.schemas.tracking import AdherenceOut, TodayItem, TodayResponse, TodaySlot
from app.services.interactions import check_pairs

SLOT_ORDER = ["morning", "afternoon", "evening", "night"]
SLOT_CUTOFF = {"morning": 11, "afternoon": 16, "evening": 21, "night": 24}


def is_valid_slot(slot: str) -> bool:
    return slot in SLOT_CUTOFF


def _day_window(now: datetime) -> tuple[datetime, datetime]:
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def build_today(session, user, now: datetime) -> TodayResponse:
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
        ing_rows = session.exec(
            select(MedicationIngredient).where(
                MedicationIngredient.medication_id.in_(list(meds.keys()))
            )
        ).all()
        for r in ing_rows:
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
        slot_scheds = [s for s in schedules if s.slot == slot]
        items: list[TodayItem] = []
        for s in slot_scheds:
            med = meds.get(s.medication_id)
            if not med:
                continue
            log = log_by_key.get((s.medication_id, slot))
            if log:
                status = log.status
            elif now.hour > SLOT_CUTOFF[slot]:
                status = "overdue"
            else:
                status = "upcoming"
            items.append(TodayItem(medication_id=med.id, name=med.name, status=status))

        # DoseGuard twist: flag interactions across the salts of meds in this slot.
        ingredients = [
            ing for s in slot_scheds for ing in ings_by_med.get(s.medication_id, [])
        ]
        warnings = [
            f"{i.ingredient_a} + {i.ingredient_b} ({i.severity})"
            for i in check_pairs(session, ingredients)
        ]
        slots_out.append(TodaySlot(slot=slot, items=items, warnings=warnings))

    adherence = compute_adherence(session, user, now=now)
    return TodayResponse(
        date=day_start.date().isoformat(),
        slots=slots_out,
        adherence=adherence.percent,
    )


def compute_adherence(session, user, days: int = 7, now: datetime | None = None) -> AdherenceOut:
    now = now or datetime.now(UTC)
    schedule_count = len(
        session.exec(
            select(DoseSchedule).where(DoseSchedule.user_id == user.id)
        ).all()
    )
    expected = schedule_count * days
    if expected == 0:
        return AdherenceOut(percent=0, taken=0, expected=0)

    since = now - timedelta(days=days)
    taken = len(
        session.exec(
            select(DoseLog).where(
                DoseLog.user_id == user.id,
                DoseLog.status == "taken",
                DoseLog.taken_at >= since,
            )
        ).all()
    )
    return AdherenceOut(percent=round(taken / expected * 100), taken=taken, expected=expected)
