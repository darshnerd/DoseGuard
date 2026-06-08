from typing import Annotated

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.deps import get_current_user
from app.models import ScanHistory, User
from app.schemas.drug import ResolvedDrug
from app.schemas.interaction import InteractionResult
from app.schemas.scan import ScanResponse
from app.services.interactions import check_pairs
from app.services.scan import detect_drugs

router = APIRouter(tags=["scan"])


@router.post("/scan", response_model=ScanResponse)
async def scan(
    image: Annotated[UploadFile, File()],
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    raw = await image.read()
    max_bytes = get_settings().max_upload_mb * 1024 * 1024
    if len(raw) > max_bytes:
        raise HTTPException(status_code=413, detail="Image too large.")

    buffer = np.frombuffer(raw, np.uint8)
    decoded = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if decoded is None:
        raise HTTPException(status_code=400, detail="Could not read image.")

    ingredients = await detect_drugs(decoded)
    detected = [
        ResolvedDrug(
            query=name,
            matched=True,
            rxcui=None,
            name=name,
            ingredient_rxcui=None,
            ingredient_name=name,
        )
        for name in ingredients
    ]
    found = check_pairs(session, ingredients)
    interactions = [
        InteractionResult(
            ingredient_a=i.ingredient_a,
            ingredient_b=i.ingredient_b,
            severity=i.severity,
            description=i.description,
        )
        for i in found
    ]

    session.add(
        ScanHistory(
            user_id=user.id,
            drugs=ingredients,
            conflict_found=bool(interactions),
            interaction_count=len(interactions),
        )
    )
    session.commit()
    
    return ScanResponse(
        detected=detected,
        ingredients=ingredients,
        conflict_found=bool(interactions),
        interactions=interactions,
    )
