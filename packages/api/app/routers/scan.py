from typing import Annotated

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.db import get_session
from app.schemas.interaction import InteractionResult
from app.schemas.scan import ScanResponse
from app.services.interactions import check_pairs
from app.services.scan import detect_drugs

router = APIRouter(tags=["scan"])


@router.post("/scan", response_model=ScanResponse)
async def scan(
    image: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_session)],
):
    raw = await image.read()
    buffer = np.frombuffer(raw, np.uint8)
    decoded = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if decoded is None:
        raise HTTPException(status_code=400, detail="Could not read image.")

    detected = await detect_drugs(decoded)
    ingredients = [d.ingredient_name.lower() for d in detected if d.ingredient_name]
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
    return ScanResponse(
        detected=detected,
        ingredients=ingredients,
        conflict_found=bool(interactions),
        interactions=interactions,
    )
    