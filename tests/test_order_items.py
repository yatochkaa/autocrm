from __future__ import annotations

import pytest
from httpx import AsyncClient


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    credentials = {"email": "items-manager@example.com", "password": "password123"}
    registered = await client.post("/auth/register", json=credentials)
    assert registered.status_code == 201, registered.text
    logged_in = await client.post("/auth/login", json=credentials)
    assert logged_in.status_code == 200, logged_in.text
    return {"Authorization": f"Bearer {logged_in.json()['access_token']}"}


async def create_lead(client: AsyncClient, headers: dict[str, str]) -> int:
    response = await client.post(
        "/leads",
        headers=headers,
        json={"name": "Заказ с позициями", "source": "manual"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.mark.asyncio
async def test_multiple_items_totals_breakdown_and_margin(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    lead_id = await create_lead(client, headers)

    original = await client.post(
        f"/leads/{lead_id}/items",
        headers=headers,
        json={
            "name": "Фара оригинальная",
            "oem": "OEM-001",
            "brand": "Lada",
            "price": 1000,
            "purchase_price": 700,
            "qty": 2,
            "is_analog": False,
        },
    )
    analog = await client.post(
        f"/leads/{lead_id}/items",
        headers=headers,
        json={
            "name": "Фара аналог",
            "brand": "TestBrand",
            "price": 600,
            "purchase_price": 400,
            "qty": 3,
            "is_analog": True,
        },
    )
    assert original.status_code == 201, original.text
    assert analog.status_code == 201, analog.text
    assert original.json()["line_total"] == 2000
    assert analog.json()["line_total"] == 1800

    response = await client.get(f"/leads/{lead_id}/items", headers=headers)
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["items"]) == 2
    assert len(body["original_items"]) == 1
    assert len(body["analog_items"]) == 1
    assert body["original_total"] == 2000
    assert body["analog_total"] == 1800
    assert body["total_amount"] == 3800
    assert body["total_margin"] == 1200

    lead = await client.get(f"/leads/{lead_id}", headers=headers)
    assert lead.status_code == 200, lead.text
    assert lead.json()["total_amount"] == 3800
    assert lead.json()["total_margin"] == 1200


@pytest.mark.asyncio
async def test_update_item_recalculates_total(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    lead_id = await create_lead(client, headers)
    created = await client.post(
        f"/leads/{lead_id}/items",
        headers=headers,
        json={"name": "Фильтр", "price": 500, "qty": 1},
    )
    item_id = created.json()["id"]

    updated = await client.patch(
        f"/leads/{lead_id}/items/{item_id}",
        headers=headers,
        json={"price": 600, "qty": 4},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["line_total"] == 2400

    summary = await client.get(f"/leads/{lead_id}/items", headers=headers)
    assert summary.json()["total_amount"] == 2400


@pytest.mark.asyncio
async def test_delete_item_removes_it_from_total(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    lead_id = await create_lead(client, headers)
    created = await client.post(
        f"/leads/{lead_id}/items",
        headers=headers,
        json={"name": "Свечи", "price": 250, "qty": 4},
    )
    item_id = created.json()["id"]

    deleted = await client.delete(
        f"/leads/{lead_id}/items/{item_id}",
        headers=headers,
    )
    assert deleted.status_code == 204, deleted.text

    summary = await client.get(f"/leads/{lead_id}/items", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["items"] == []
    assert summary.json()["total_amount"] == 0


@pytest.mark.asyncio
async def test_item_must_belong_to_lead(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    first_lead_id = await create_lead(client, headers)
    second_lead_id = await create_lead(client, headers)
    created = await client.post(
        f"/leads/{first_lead_id}/items",
        headers=headers,
        json={"name": "Ремень", "price": 900, "qty": 1},
    )
    item_id = created.json()["id"]

    response = await client.patch(
        f"/leads/{second_lead_id}/items/{item_id}",
        headers=headers,
        json={"qty": 2},
    )
    assert response.status_code == 404
