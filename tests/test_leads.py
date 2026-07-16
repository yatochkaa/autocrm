from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_normalizes_phone_and_extracts_vin(
    lead_factory,
) -> None:
    lead = await lead_factory(
        name="Иван",
        phone="8 (999) 123-45-67",
        source="telegram",
        car_info="Lada Vesta, VIN XTA210990Y2765432",
    )
    assert lead["phone"] == "+79991234567"
    assert lead["vin"] == "XTA210990Y2765432"
    assert lead["status"] == "new"


@pytest.mark.asyncio
async def test_invalid_vin_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.post(
        "/leads",
        headers=auth_headers,
        json={"name": "Иван", "vin": "SHORTVIN"},
    )
    assert response.status_code == 422
    assert "17" in response.json()["detail"]


@pytest.mark.asyncio
async def test_leads_require_authentication(client: AsyncClient) -> None:
    response = await client.get("/leads")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_filters_by_status_source_and_manager(
    client: AsyncClient,
    lead_factory,
    auth_user: dict[str, object],
) -> None:
    telegram = await lead_factory(name="Telegram", source="telegram")
    await lead_factory(name="Site", source="site")
    changed = await client.patch(
        f"/leads/{telegram['id']}/status",
        headers=auth_user["headers"],
        json={"status": "in_progress"},
    )
    assert changed.status_code == 200

    response = await client.get(
        "/leads",
        headers=auth_user["headers"],
        params={
            "status": "in_progress",
            "source": "telegram",
            "manager_id": auth_user["id"],
        },
    )
    assert response.status_code == 200
    assert [lead["id"] for lead in response.json()] == [telegram["id"]]


@pytest.mark.asyncio
async def test_get_and_update_lead(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
) -> None:
    lead = await lead_factory(name="До изменения")
    loaded = await client.get(f"/leads/{lead['id']}", headers=auth_headers)
    assert loaded.status_code == 200

    updated = await client.patch(
        f"/leads/{lead['id']}",
        headers=auth_headers,
        json={"name": "После изменения", "phone": "89991112233"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "После изменения"
    assert updated.json()["phone"] == "+79991112233"


@pytest.mark.asyncio
async def test_status_change_writes_history(
    client: AsyncClient,
    auth_user: dict[str, object],
    lead_factory,
) -> None:
    lead = await lead_factory()
    response = await client.patch(
        f"/leads/{lead['id']}/status",
        headers=auth_user["headers"],
        json={"status": "in_progress"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "in_progress"
    assert body["history"][-1]["from_status"] == "new"
    assert body["history"][-1]["to_status"] == "in_progress"
    assert body["history"][-1]["changed_by"] == auth_user["id"]


@pytest.mark.asyncio
async def test_invalid_status_jump_returns_409(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
) -> None:
    lead = await lead_factory()
    response = await client.patch(
        f"/leads/{lead['id']}/status",
        headers=auth_headers,
        json={"status": "won"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_lead(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
) -> None:
    lead = await lead_factory()
    deleted = await client.delete(f"/leads/{lead['id']}", headers=auth_headers)
    assert deleted.status_code == 204

    loaded = await client.get(f"/leads/{lead['id']}", headers=auth_headers)
    assert loaded.status_code == 404
