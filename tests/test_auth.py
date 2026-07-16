import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.api.dependencies.auth import require_role
from app.db.enums import UserRole
from app.db.models.user import User


async def register(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/register",
        json={"email": "manager@example.com", "password": "strongpass123"},
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_successful_login_and_me(client: AsyncClient) -> None:
    await register(client)
    login = await client.post(
        "/auth/login",
        json={"email": "manager@example.com", "password": "strongpass123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "manager@example.com"
    assert me.json()["role"] == "manager"


@pytest.mark.asyncio
async def test_wrong_password(client: AsyncClient) -> None:
    await register(client)
    response = await client.post(
        "/auth/login",
        json={"email": "manager@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_without_token(client: AsyncClient) -> None:
    response = await client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_require_admin_role_rejects_manager() -> None:
    guard = require_role(UserRole.ADMIN)
    manager = User(email="manager@example.com", password_hash="x", role=UserRole.MANAGER)
    with pytest.raises(HTTPException) as error:
        await guard(manager)
    assert error.value.status_code == 403
