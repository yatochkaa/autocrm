from __future__ import annotations

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.api.dependencies.auth import require_role
from app.db.enums import UserRole
from app.db.models.user import User


@pytest.mark.asyncio
async def test_successful_login_and_me(
    client: AsyncClient,
    auth_user: dict[str, object],
) -> None:
    response = await client.get("/auth/me", headers=auth_user["headers"])
    assert response.status_code == 200
    assert response.json()["email"] == auth_user["email"]
    assert response.json()["role"] == "manager"


@pytest.mark.asyncio
async def test_duplicate_registration_returns_409(
    client: AsyncClient,
    auth_user: dict[str, object],
) -> None:
    response = await client.post(
        "/auth/register",
        json={
            "email": auth_user["email"],
            "password": auth_user["password"],
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_registration_normalizes_email(client: AsyncClient, user_factory) -> None:
    user = await user_factory(email="  Manager@Test.Example  ")
    assert user["email"] == "manager@test.example"


@pytest.mark.asyncio
async def test_wrong_password(
    client: AsyncClient,
    auth_user: dict[str, object],
) -> None:
    response = await client.post(
        "/auth/login",
        json={"email": auth_user["email"], "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_require_admin_role_rejects_manager() -> None:
    guard = require_role(UserRole.ADMIN)
    manager = User(
        email="manager@example.com",
        password_hash="x",
        role=UserRole.MANAGER,
    )
    with pytest.raises(HTTPException) as error:
        await guard(manager)
    assert error.value.status_code == 403
