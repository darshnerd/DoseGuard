from typing import Annotated

from fastapi import APIRouter, Query

from app.schemas.drug import ResolvedDrug
from app.services.rxnorm import RxNormClient

router = APIRouter(prefix="/drugs", tags=["drugs"])

@router.get("/resolve", response_model=ResolvedDrug)
async def resolved_drug(q: Annotated[str, Query(min_length=1)]):
    return await RxNormClient().resolve(q)
