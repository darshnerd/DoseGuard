import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import get_settings

settings = get_settings()


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _create_token(subject, version, expires_delta, token_type):
    now = datetime.now(UTC)
    payload = {
        "sub": str(subject),
        "ver": version,
        "type": token_type,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject, version):
    return _create_token(
        subject, version, timedelta(minutes=settings.access_token_minutes), "access"
    )


def create_refresh_token(subject, version):
    return _create_token(
        subject, version, timedelta(days=settings.refresh_token_days), "refresh"
    )


def decode_token(token):
    return jwt.decode(
        token, settings.secret_key, algorithms=[settings.jwt_algorithm], leeway=10
    )
