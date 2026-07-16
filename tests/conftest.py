from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Awaitable, Callable
from itertools import count
from typing import Any, TypedDict

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.core.database import get_session
from app.db.models import Base
from app.main import app

DEFAULT_TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class TestUser(TypedDict):
    id: int
    email: str
    password: str
    headers: dict[str, str]


UserFactory = Callable[..., Awaitable[TestUser]]
LeadFactory = Callable[..., Awaitable[dict[str, Any]]]
OrderItemFactory = Callable[..., Awaitable[dict[str, Any]]]


@pytest_asyncio.fixture
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Свежая схема на SQLite локально или PostgreSQL в CI."""
    database_url = os.getenv("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)
    engine_kwargs: dict[str, Any] = {}
    if database_url.startswith("sqlite"):
        engine_kwargs.update(
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

    engine = create_async_engine(database_url, **engine_kwargs)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(
    db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture
async def client(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def user_factory(client: AsyncClient) -> UserFactory:
    sequence = count(1)

    async def factory(
        email: str | None = None,
        password: str = "password123",
    ) -> TestUser:
        user_email = email or f"manager-{next(sequence)}@example.com"
        registered = await client.post(
            "/auth/register",
            json={"email": user_email, "password": password},
        )
        assert registered.status_code == 201, registered.text

        logged_in = await client.post(
            "/auth/login",
            json={"email": user_email.strip().lower(), "password": password},
        )
        assert logged_in.status_code == 200, logged_in.text
        return {
            "id": registered.json()["id"],
            "email": registered.json()["email"],
            "password": password,
            "headers": {"Authorization": f"Bearer {logged_in.json()['access_token']}"},
        }

    return factory


@pytest_asyncio.fixture
async def auth_user(user_factory: UserFactory) -> TestUser:
    return await user_factory()


@pytest.fixture
def auth_headers(auth_user: TestUser) -> dict[str, str]:
    return auth_user["headers"]


@pytest.fixture
def lead_factory(client: AsyncClient, auth_headers: dict[str, str]) -> LeadFactory:
    async def factory(
        *,
        headers: dict[str, str] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": "Тестовая заявка",
            "source": "manual",
        }
        payload.update(overrides)
        response = await client.post(
            "/leads",
            headers=headers or auth_headers,
            json=payload,
        )
        assert response.status_code == 201, response.text
        return response.json()

    return factory


@pytest.fixture
def order_item_factory(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> OrderItemFactory:
    async def factory(
        lead_id: int,
        *,
        headers: dict[str, str] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": "Тестовая деталь",
            "price": 100,
            "qty": 1,
            "is_analog": False,
        }
        payload.update(overrides)
        response = await client.post(
            f"/leads/{lead_id}/items",
            headers=headers or auth_headers,
            json=payload,
        )
        assert response.status_code == 201, response.text
        return response.json()

    return factory
