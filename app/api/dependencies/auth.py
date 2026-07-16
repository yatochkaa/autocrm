"""Получение текущего пользователя и проверка ролей."""
from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import decode_access_token
from app.db.enums import UserRole
from app.db.models.user import User
from app.repositories.user import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить авторизацию",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_error()

    try:
        user_id = decode_access_token(credentials.credentials)
    except jwt.InvalidTokenError as error:
        raise credentials_error() from error

    user = await UserRepository(session).get_by_id(user_id)
    if user is None:
        raise credentials_error()
    return user


def require_role(
    *allowed_roles: UserRole,
) -> Callable[[User], Coroutine[Any, Any, User]]:
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав")
        return current_user

    return role_checker
