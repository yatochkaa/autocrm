from __future__ import annotations

import pytest
from httpx import AsyncClient


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    credentials = {"email": "lead-manager@example.com", "password": "password123"}
    registered = await client.post("/auth/register", json=credentials)
    assert registered.status_code == 201, registered.text
    logged_in = await client.post("/auth/login", json=credentials)
    assert logged_in.status_code == 200, logged_in.text
    token = logged_in.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_normalizes_phone_and_extracts_vin(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    response = await client.post(
        "/leads",
        headers=headers,
        json={
            "name": "Иван",
            "phone": "8 (999) 123-45-67",
            "source": "telegram",
            "car_info": "Lada Vesta, VIN XTA210990Y2765432",
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["phone"] == "+79991234567"
    assert body["vin"] == "XTA210990Y2765432"
    assert body["status"] == "new"


@pytest.mark.asyncio
async def test_invalid_vin_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    response = await client.post(
        "/leads",
        headers=headers,
        json={"name": "Иван", "vin": "SHORTVIN"},
    )
    assert response.status_code == 422
    assert "17" in response.json()["detail"]


@pytest.mark.asyncio
async def test_status_change_writes_history(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    created = await client.post("/leads", headers=headers, json={"name": "Иван"})
    lead_id = created.json()["id"]

    changed = await client.patch(
        f"/leads/{lead_id}/status",
        headers=headers,
        json={"status": "in_progress"},
    )

    assert changed.status_code == 200, changed.text
    body = changed.json()
    assert body["status"] == "in_progress"
    assert len(body["history"]) == 1
    assert body["history"][0]["from_status"] == "new"
    assert body["history"][0]["to_status"] == "in_progress"
    assert body["history"][0]["changed_by"] is not None


@pytest.mark.asyncio
async def test_invalid_status_jump_returns_409(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    created = await client.post("/leads", headers=headers, json={"name": "Иван"})
    lead_id = created.json()["id"]

    response = await client.patch(
        f"/leads/{lead_id}/status",
        headers=headers,
        json={"status": "won"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_filters_and_update(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    first = await client.post(
        "/leads",
        headers=headers,
        json={"name": "Telegram lead", "source": "telegram"},
    )
    await client.post(
        "/leads",
        headers=headers,
        json={"name": "Site lead", "source": "site"},
    )

    filtered = await client.get("/leads?source=telegram&status=new", headers=headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1

    lead_id = first.json()["id"]
    updated = await client.patch(
        f"/leads/{lead_id}",
        headers=headers,
        json={"name": "Updated lead"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated lead"
