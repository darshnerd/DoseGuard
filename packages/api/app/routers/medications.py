from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_current_user
from app.models import DoseSchedule, Medication, MedicationIngredient, User
from app.schemas.interaction import InteractionCheckResponse, InteractionResult
from app.schemas.medication import IngredientOut, MedicationCreate, MedicationOut
from app.services.interactions import check_pairs
from app.services.rxnorm import RxNormClient

router = APIRouter(prefix="/medications", tags=["medications"])


def _med_out(session: Session, med: Medication) -> MedicationOut:
    rows = session.exec(
        select(MedicationIngredient).where(MedicationIngredient.medication_id == med.id)
    ).all()
    return MedicationOut(
        id=med.id,
        name=med.name,
        ingredients=[IngredientOut(ingredient=r.ingredient, rxcui=r.rxcui) for r in rows],
    )


@router.post("", response_model=MedicationOut, status_code=status.HTTP_201_CREATED)
async def add_medication(
    req: MedicationCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    med = Medication(user_id=user.id, name=req.name)
    session.add(med)
    session.commit()
    session.refresh(med)

    # Resolve each source drug into a salt. One scan (many drugs) => one med
    # with many MedicationIngredient rows.
    sources = req.drugs if req.drugs else [req.name]
    client = RxNormClient()
    seen: set[str] = set()
    for src in sources:
        if not src or not src.strip():
            continue
        resolved = await client.resolve(src)
        ingredient = (resolved.ingredient_name or src).lower()
        if ingredient in seen:
            continue
        seen.add(ingredient)
        session.add(
            MedicationIngredient(
                medication_id=med.id,
                ingredient=ingredient,
                rxcui=resolved.rxcui,
            )
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


@router.delete("/{med_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    med_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    med = session.get(Medication, med_id)
    if not med or med.user_id != user.id:
        raise HTTPException(status_code=404, detail="Medication not found.")
    # Clean up salts and schedules tied to this med (dose logs kept as history).
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
    ingredients = [r.ingredient for r in rows]
    found = check_pairs(session, ingredients)
    results = [
        InteractionResult(
            ingredient_a=i.ingredient_a,
            ingredient_b=i.ingredient_b,
            severity=i.severity,
            description=i.description,
        )
        for i in found
    ]
    return InteractionCheckResponse(
        drugs=[m.name for m in meds],
        ingredients=ingredients,
        conflict_found=bool(results),
        interactions=results,
    )
    