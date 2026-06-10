from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db import get_session
from app.schemas.drug import ResolvedDrug
from app.services.rxnorm import RxNormClient
from app.services.search import search_drugs

router = APIRouter(prefix="/drugs", tags=["drugs"])


@router.get("/resolve", response_model=ResolvedDrug)
async def resolved_drug(q: Annotated[str, Query(min_length=1)]):
    return await RxNormClient().resolve(q)


@router.get("/search")
def search(
    q: Annotated[str, Query(min_length=1)],
    session: Annotated[Session, Depends(get_session)],
):
    return search_drugs(session, q)