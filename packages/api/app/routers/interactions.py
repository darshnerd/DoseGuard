from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas.interaction import (
    InteractionCheckRequest,
    InteractionCheckResponse,
    InteractionResult,
)
from app.services.interactions import check_pairs
from app.services.rxnorm import RxNormClient

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/check", response_model=InteractionCheckResponse)
async def check_interactions(
    req: InteractionCheckRequest,
    session: Annotated[Session, Depends(get_session)],
):
    client = RxNormClient()

    ingredients = []
    for drug in req.drugs:
        resolved = await client.resolve(drug)
        names = resolved.ingredient_names or (
            [resolved.ingredient_name] if resolved.ingredient_name else []
        )
        ingredients.extend(names)

    found = check_pairs(session, ingredients)
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
        drugs=req.drugs,
        ingredients=ingredients,
        conflict_found=bool(results),
        interactions=results,
    )
    