"""Бизнес-логика регистрации и входа."""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.enums import UserRole
from app.db.models.user import User
from app.repositories.user import UserRepository


class EmailAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    async def register(self, email: str, password: str) -> User:
        normalized_email = email.strip().lower()
        if await self.users.get_by_email(normalized_email):
            raise EmailAlreadyExistsError

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            role=UserRole.MANAGER,
        )
        return await self.users.create(user)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.users.get_by_email(email.strip().lower())
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError
        return user
