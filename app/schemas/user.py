"""Схемы пользователя (create / read / update)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.enums import UserRole


class UserBase(BaseModel):
    # email как str, чтобы не тянуть email-validator; при желании -> EmailStr.
    email: str = Field(max_length=255)
    role: UserRole = UserRole.MANAGER


class UserCreate(UserBase):
    # На вход — пароль в открытом виде; сервис захеширует его в password_hash.
    password: str = Field(min_length=6, max_length=128)


class UserUpdate(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    role: UserRole | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
