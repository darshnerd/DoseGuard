from datetime import UTC, datetime, timedelta
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_current_user
from app.models import DoseLog, DoseSchedule, Medication, User
from app.schemas.tracking import (
    AdherenceOut,
    DayStat,
    LogCreate,
    ScheduleOut,
    ScheduleUpdate,
    TodayResponse,
)
from app.services.tracking import build_today, compute_adherence, daily_history, is_valid_slot

router = APIRouter(prefix="/tracking", tags=["tracking"])


def _user_now(user: User) -> datetime:
    try:
        tz = ZoneInfo(user.timezone or "Asia/Kolkata")
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")
    return datetime.now(tz)


def _owned_medication(session: Session, user: User, medication_id: int) -> Medication:
    med = session.get(Medication, medication_id)
    if not med or med.user_id != user.id:
        raise HTTPException(status_code=404, detail="Medication not found.")
    return med


@router.get("/today", response_model=TodayResponse)
def get_today(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    return build_today(session, user, _user_now(user))


@router.get("/schedule", response_model=list[ScheduleOut])
def get_schedule(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    meds = {
        m.id: m
        for m in session.exec(select(Medication).where(Medication.user_id == user.id)).all()
    }
    schedules = session.exec(
        select(DoseSchedule).where(DoseSchedule.user_id == user.id)
    ).all()

    grouped: dict[int, list[str]] = {}
    for s in schedules:
        grouped.setdefault(s.medication_id, []).append(s.slot)

    return [
        ScheduleOut(medication_id=med_id, name=meds[med_id].name, slots=slots)
        for med_id, slots in grouped.items()
        if med_id in meds
    ]


@router.put("/schedule/{medication_id}", response_model=ScheduleOut)
def set_schedule(
    medication_id: int,
    req: ScheduleUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    med = _owned_medication(session, user, medication_id)

    slots = []
    for slot in req.slots:
        if not is_valid_slot(slot):
            raise HTTPException(status_code=422, detail=f"Invalid slot: {slot}")
        if slot not in slots:
            slots.append(slot)

    existing = session.exec(
        select(DoseSchedule).where(
            DoseSchedule.user_id == user.id,
            DoseSchedule.medication_id == medication_id,
        )
    ).all()
    for row in existing:
        session.delete(row)
    for slot in slots:
        session.add(DoseSchedule(user_id=user.id, medication_id=medication_id, slot=slot))
    session.commit()

    return ScheduleOut(medication_id=medication_id, name=med.name, slots=slots)


@router.post("/log", status_code=status.HTTP_201_CREATED)
def log_dose(
    req: LogCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    if not is_valid_slot(req.slot):
        raise HTTPException(status_code=422, detail=f"Invalid slot: {req.slot}")
    if req.status not in ("taken", "skipped"):
        raise HTTPException(status_code=422, detail="status must be taken or skipped.")
    _owned_medication(session, user, req.medication_id)

    # One log per (med, slot) per LOCAL day; taken_at itself is stored in UTC.
    now_local = _user_now(user)
    local_midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
    day_start = local_midnight.astimezone(UTC)
    day_end = (local_midnight + timedelta(days=1)).astimezone(UTC)
    log = session.exec(
        select(DoseLog).where(
            DoseLog.user_id == user.id,
            DoseLog.medication_id == req.medication_id,
            DoseLog.slot == req.slot,
            DoseLog.taken_at >= day_start,
            DoseLog.taken_at < day_end,
        )
    ).first()
    now_utc = datetime.now(UTC)
    if log:
        log.status = req.status
        log.taken_at = now_utc
    else:
        log = DoseLog(
            user_id=user.id,
            medication_id=req.medication_id,
            slot=req.slot,
            status=req.status,
            taken_at=now_utc,
        )
    session.add(log)
    session.commit()
    session.refresh(log)
    return {"id": log.id}


@router.delete("/log/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_log(
    log_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    log = session.get(DoseLog, log_id)
    if not log or log.user_id != user.id:
        raise HTTPException(status_code=404, detail="Log not found.")
    session.delete(log)
    session.commit()


@router.get("/adherence", response_model=AdherenceOut)
def get_adherence(
    days: Annotated[int, Query(ge=1, le=90)] = 7,
    user: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[Session, Depends(get_session)] = None,
):
    return compute_adherence(session, user, days=days, now=_user_now(user))


@router.get("/history", response_model=list[DayStat])
def get_history(
    days: Annotated[int, Query(ge=1, le=90)] = 30,
    user: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[Session, Depends(get_session)] = None,
):
    return daily_history(session, user, days=days, now=_user_now(user))
