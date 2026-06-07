from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_current_user
from app.models import Medication, User
from app.schemas.interaction import InteractionCheckResponse, InteractionResult
from app.schemas.medication import MedicationCreate, MedicationOut
from app.services.interactions import check_pairs
from app.services.rxnorm import RxNormClient

router = APIRouter(prefix="/medications", tags=["medications"])


@router.post("", response_model=MedicationOut, status_code=status.HTTP_201_CREATED)
async def add_medication(
    req: MedicationCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    resolved = await RxNormClient().resolve(req.name)
    med = Medication(
        user_id=user.id,
        name=req.name,
        ingredient=resolved.ingredient_name.lower() if resolved.ingredient_name else None,
        rxcui=resolved.rxcui,
    )
    session.add(med)
    session.commit()
    session.refresh(med)
    return med


@router.get("", response_model=list[MedicationOut])
def list_medications(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    return session.exec(select(Medication).where(Medication.user_id == user.id)).all()


@router.delete("/{med_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medication(
    med_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    med = session.get(Medication, med_id)
    if not med or med.user_id != user.id:
        raise HTTPException(status_code=404, detail="Medication not found.")
    session.delete(med)
    session.commit()


@router.get("/check", response_model=InteractionCheckResponse)
def check_my_medications(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    meds = session.exec(select(Medication).where(Medication.user_id == user.id)).all()
    ingredients = [m.ingredient for m in meds if m.ingredient]
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