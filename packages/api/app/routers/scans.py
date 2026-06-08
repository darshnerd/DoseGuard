from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_current_user
from app.models import ScanHistory, User
from app.schemas.scan import ScanRecordOut

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("", response_model=list[ScanRecordOut])
def list_scans(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    stmt = (
        select(ScanHistory)
        .where(ScanHistory.user_id == user.id)
        .order_by(ScanHistory.created_at.desc())
    )
    return session.exec(stmt).all()


@router.delete("/{scan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scan(
    scan_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    record = session.get(ScanHistory, scan_id)
    if not record or record.user_id != user.id:
        raise HTTPException(status_code=404, detail="Scan not found.")
    session.delete(record)
    session.commit()
    