"""HTTP-эндпоинты авторизации."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, status
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

router = APIRouter(prefix="/auth", tags=["Авторизация"])

REGISTER_EXAMPLES = {
    "Регистрация": {
        "summary": "Регистрация нового менеджера",
        "value": {"email": "manager@autocrm.ru", "password": "SecurePass123"},
    }
}

LOGIN_EXAMPLES = {
    "Вход": {
        "summary": "Вход по email и паролю",
        "value": {"email": "manager@autocrm.ru", "password": "SecurePass123"},
    }
}


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="Создаёт нового пользователя (менеджера) по email и паролю.",
    responses={
        201: {"description": "Пользователь успешно создан"},
        409: {"description": "Пользователь с таким email уже существует"},
        422: {"description": "Ошибка валидации входных данных"},
    },
)
async def register(
    data: Annotated[UserRegister, Body(openapi_examples=REGISTER_EXAMPLES)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    try:
        return await AuthService(session).register(data.email, data.password)
    except EmailAlreadyExistsError as error:
        raise HTTPException(
            status_code=409, detail="Пользователь уже существует"
        ) from error


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход и получение токена",
    description=(
        "Проверяет email и пароль и возвращает JWT `access_token` "
        "для авторизации в защищённых эндпоинтах."
    ),
    responses={
        200: {"description": "Успешный вход, возвращён access_token"},
        401: {"description": "Неверный email или пароль"},
        422: {"description": "Ошибка валидации входных данных"},
    },
)
async def login(
    data: Annotated[LoginRequest, Body(openapi_examples=LOGIN_EXAMPLES)],
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


@router.get(
    "/me",
    response_model=UserRead,
    summary="Текущий пользователь",
    description="Возвращает данные авторизованного пользователя по токену.",
    responses={
        200: {"description": "Данные текущего пользователя"},
        401: {"description": "Не авторизован — требуется валидный токен"},
    },
)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
