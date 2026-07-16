"""Хеширование паролей и работа с JWT access-токенами."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from app.core.config import settings

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return password_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return password_context.verify(password, password_hash)


def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int:
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    subject = payload.get("sub")
    if subject is None:
        raise jwt.InvalidTokenError("Token subject is missing")
    try:
        return int(subject)
    except (TypeError, ValueError) as error:
        raise jwt.InvalidTokenError("Invalid token subject") from error
