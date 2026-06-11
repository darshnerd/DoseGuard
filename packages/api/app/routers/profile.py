from typing import Annotated
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db import get_session
from app.deps import get_current_user
from app.models import User
from app.schemas.profile import ProfileOut, ProfileUpdate

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(user: Annotated[User, Depends(get_current_user)]):
    return user


@router.patch("", response_model=ProfileOut)
def update_profile(
    req: ProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    data = req.model_dump(exclude_unset=True)
    if data.get("timezone") is not None:
        try:
            ZoneInfo(data["timezone"])
        except (ZoneInfoNotFoundError, ValueError):
            raise HTTPException(status_code=422, detail="Invalid timezone.") from None
    for key, value in data.items():
        setattr(user, key, value)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
