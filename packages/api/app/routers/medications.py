from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_current_user
from app.models import DoseSchedule, Medication, MedicationIngredient, User
from app.normalize import split_components
from app.schemas.interaction import InteractionCheckResponse, InteractionResult
from app.schemas.medication import IngredientOut, MedicationCreate, MedicationOut, MedicationUpdate
from app.services.interactions import check_pairs_grouped
from app.services.rxnorm import RxNormClient

router = APIRouter(prefix="/medications", tags=["medications"])


def _med_out(session: Session, med: Medication) -> MedicationOut:
    rows = session.exec(
        select(MedicationIngredient).where(MedicationIngredient.medication_id == med.id)
    ).all()
    return MedicationOut(
        id=med.id,
        name=med.name,
        start_date=med.start_date,
        duration_days=med.duration_days,
        ingredients=[IngredientOut(ingredient=r.ingredient, rxcui=r.rxcui) for r in rows],
    )


def _owned(session: Session, user: User, med_id: int) -> Medication:
    med = session.get(Medication, med_id)
    if not med or med.user_id != user.id:
        raise HTTPException(status_code=404, detail="Medication not found.")
    return med


@router.post("", response_model=MedicationOut, status_code=status.HTTP_201_CREATED)
async def add_medication(
    req: MedicationCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    # Block duplicates — same medicine can't be added twice (case-insensitive).
    target = req.name.strip().lower()
    existing = session.exec(select(Medication).where(Medication.user_id == user.id)).all()
    if any(m.name.strip().lower() == target for m in existing):
        raise HTTPException(status_code=409, detail="This medication is already in your list.")

    med = Medication(
        user_id=user.id,
        name=req.name,
        start_date=req.start_date or datetime.now(UTC).date(),
        duration_days=req.duration_days,
    )
    session.add(med)
    session.commit()
    session.refresh(med)

    # Resolve each source drug into a salt. One scan (many drugs) => one med
    # with many MedicationIngredient rows.
    raw_sources = req.drugs if req.drugs else [req.name]
    sources = [c for s in raw_sources for c in (split_components(s) or [s])]

    client = RxNormClient()
    seen: set[str] = set()
    for src in sources:
        if not src or not src.strip():
            continue
        resolved = await client.resolve(src)
        names = resolved.ingredient_names or [(resolved.ingredient_name or src).lower()]
        for ingredient in names:
            ingredient = ingredient.lower()
            if ingredient in seen:
                continue
            seen.add(ingredient)
            session.add(
                MedicationIngredient(medication_id=med.id, ingredient=ingredient, rxcui=resolved.rxcui)
            )
    session.commit()
    session.refresh(med)
    return _med_out(session, med)


@router.get("", response_model=list[MedicationOut])
def list_medications(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    meds = session.exec(select(Medication).where(Medication.user_id == user.id)).all()
    return [_med_out(session, m) for m in meds]


@router.patch("/{med_id}", response_model=MedicationOut)
def update_medication(
    med_id: int,
    req: MedicationUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    med = _owned(session, user, med_id)
    data = req.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        med.name = data["name"]
    if data.get("duration_days") is not None:
        med.duration_days = data["duration_days"]
    if "start_date" in data and data["start_date"]:
        med.start_date = data["start_date"]
    session.add(med)
    session.commit()
    session.refresh(med)
    return _med_out(session, med)


@router.delete("/{med_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    med_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    med = _owned(session, user, med_id)
    for row in session.exec(
        select(MedicationIngredient).where(MedicationIngredient.medication_id == med_id)
    ).all():
        session.delete(row)
    for sched in session.exec(
        select(DoseSchedule).where(DoseSchedule.medication_id == med_id)
    ).all():
        session.delete(sched)
    session.delete(med)
    session.commit()


@router.get("/check", response_model=InteractionCheckResponse)
def check_my_medications(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    meds = session.exec(select(Medication).where(Medication.user_id == user.id)).all()
    rows = session.exec(
        select(MedicationIngredient)
        .join(Medication, MedicationIngredient.medication_id == Medication.id)
        .where(Medication.user_id == user.id)
    ).all()

    groups: dict[int, list[str]] = {}
    for r in rows:
        groups.setdefault(r.medication_id, []).append(r.ingredient)
    ingredients = [ing for g in groups.values() for ing in g]
    found = check_pairs_grouped(session, list(groups.values()))

    results = [
        InteractionResult(
            ingredient_a=i.a_norm,
            ingredient_b=i.b_norm,
            severity=i.severity,
            description=i.description,
            mechanism=i.mechanism,
            source=i.sources or None,
        )
        for i in found
    ]
    return InteractionCheckResponse(
        drugs=[m.name for m in meds],
        ingredients=ingredients,
        conflict_found=bool(results),
        interactions=results,
    )
