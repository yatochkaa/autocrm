"""Administrator settings and manager account management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.database import get_session
from app.core.runtime_settings import RuntimeSettings, load_runtime_settings, save_runtime_settings
from app.core.security import hash_password
from app.core.user_profiles import normalize_username, profile_for, set_profile
from app.db.enums import UserRole
from app.db.models.lead import Lead
from app.db.models.user import User
from app.schemas.settings import ManagerCreate, ManagerUpdate, RuntimeSettingsOut, RuntimeSettingsUpdate, UserSummary

router = APIRouter(prefix="/settings", tags=["settings"])
SessionDep = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Только для директора")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]


@router.get("", response_model=RuntimeSettingsOut)
async def get_runtime_settings(_current_user: CurrentUser) -> RuntimeSettings:
    return load_runtime_settings()


@router.patch("", response_model=RuntimeSettingsOut)
async def update_runtime_settings(body: RuntimeSettingsUpdate, _admin: AdminUser) -> RuntimeSettings:
    if not body.normal_after_minutes < body.high_after_minutes < body.urgent_after_minutes:
        raise HTTPException(status_code=422, detail="Пороги должны идти по возрастанию")
    return save_runtime_settings(RuntimeSettings(**body.model_dump()))


async def user_summary(user: User, session: AsyncSession) -> UserSummary:
    total = await session.scalar(select(func.count(Lead.id)).where(Lead.manager_id == user.id))
    active = await session.scalar(select(func.count(Lead.id)).where(Lead.manager_id == user.id, Lead.status.notin_(["won", "lost"])))
    profile = profile_for(user.id, user.email, user.role.value)
    return UserSummary(
        id=user.id,
        email=user.email,
        username=profile.username,
        full_name=profile.full_name,
        role=user.role.value,
        total_leads=int(total or 0),
        active_leads=int(active or 0),
    )


@router.get("/users", response_model=list[UserSummary])
async def list_users(session: SessionDep, _current_user: CurrentUser) -> list[UserSummary]:
    users = list((await session.scalars(select(User).order_by(User.id))).all())
    return [await user_summary(user, session) for user in users]


@router.post("/users", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
async def create_manager(body: ManagerCreate, session: SessionDep, _admin: AdminUser) -> UserSummary:
    try:
        username = normalize_username(body.username)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    email = f"{username}@autocrm.local"
    if await session.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Такой логин уже существует")
    user = User(email=email, password_hash=hash_password(body.password), role=UserRole.MANAGER)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    try:
        set_profile(user.id, username, body.full_name)
    except ValueError as error:
        await session.delete(user)
        await session.commit()
        raise HTTPException(status_code=422, detail=str(error)) from error
    return await user_summary(user, session)


@router.patch("/users/{user_id}", response_model=UserSummary)
async def update_manager(user_id: int, body: ManagerUpdate, session: SessionDep, _admin: AdminUser) -> UserSummary:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.role == UserRole.ADMIN:
        raise HTTPException(status_code=409, detail="Данные директора меняются через ENV/seed")
    try:
        username = normalize_username(body.username)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    email = f"{username}@autocrm.local"
    duplicate = await session.scalar(select(User).where(User.email == email, User.id != user.id))
    if duplicate:
        raise HTTPException(status_code=409, detail="Такой логин уже существует")
    user.email = email
    if body.password:
        user.password_hash = hash_password(body.password)
    await session.commit()
    await session.refresh(user)
    try:
        set_profile(user.id, username, body.full_name)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return await user_summary(user, session)
