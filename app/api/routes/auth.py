"""HTTP-эндпоинты авторизации."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.core.security import create_access_token
from app.db.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserRegister
from app.schemas.user import UserRead
from app.services.auth import (
    AuthService,
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    try:
        return await AuthService(session).register(data.email, data.password)
    except EmailAlreadyExistsError as error:
        raise HTTPException(
            status_code=409, detail="Пользователь уже существует"
        ) from error


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TokenResponse:
    try:
        user = await AuthService(session).authenticate(data.email, data.password)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=401,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
