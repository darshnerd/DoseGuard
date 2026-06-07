from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.db import get_session
from app.deps import get_current_user
from app.models import User
from app.ratelimit import limiter
from app.schemas.auth import RefreshRequest, RegisterRequest, TokenPair, UserOut
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_tokens(user):
    return TokenPair(
        access_token=create_access_token(user.id, user.token_version),
        refresh_token=create_refresh_token(user.id, user.token_version),
    )


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(
    request: Request,
    req: RegisterRequest,
    session: Annotated[Session, Depends(get_session)],
):
    existing = session.exec(select(User).where(User.email == req.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = User(email=req.email, hashed_password=hash_password(req.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
@limiter.limit("5/minute")
def login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    user = session.exec(select(User).where(User.email == form.username)).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
@limiter.limit("10/minute")
def refresh(
    request: Request,
    req: RefreshRequest,
    session: Annotated[Session, Depends(get_session)],
):
    try:
        payload = decode_token(req.refresh_token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token.") from None
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    user = session.get(User, int(payload["sub"]))
    if not user or payload.get("ver") != user.token_version:
        raise HTTPException(status_code=401, detail="Invalid refresh token.")
    return _issue_tokens(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_session)],
):
    user.token_version += 1
    session.add(user)
    session.commit()