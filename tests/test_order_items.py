from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_multiple_items_totals_breakdown_and_margin(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
    order_item_factory,
) -> None:
    lead = await lead_factory(name="Заказ с позициями")
    original = await order_item_factory(
        lead["id"],
        name="Фара оригинальная",
        price=1000,
        purchase_price=700,
        qty=2,
        is_analog=False,
    )
    analog = await order_item_factory(
        lead["id"],
        name="Фара аналог",
        price=600,
        purchase_price=400,
        qty=3,
        is_analog=True,
    )
    assert original["line_total"] == 2000
    assert analog["line_total"] == 1800

    response = await client.get(f"/leads/{lead['id']}/items", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["original_items"]) == 1
    assert len(body["analog_items"]) == 1
    assert body["original_total"] == 2000
    assert body["analog_total"] == 1800
    assert body["total_amount"] == 3800
    assert body["total_margin"] == 1200


@pytest.mark.asyncio
async def test_update_item_recalculates_total(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
    order_item_factory,
) -> None:
    lead = await lead_factory()
    item = await order_item_factory(lead["id"], price=500, qty=1)
    updated = await client.patch(
        f"/leads/{lead['id']}/items/{item['id']}",
        headers=auth_headers,
        json={"price": 600, "qty": 4},
    )
    assert updated.status_code == 200
    assert updated.json()["line_total"] == 2400

    summary = await client.get(f"/leads/{lead['id']}/items", headers=auth_headers)
    assert summary.json()["total_amount"] == 2400


@pytest.mark.asyncio
async def test_delete_item_removes_it_from_total(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
    order_item_factory,
) -> None:
    lead = await lead_factory()
    item = await order_item_factory(lead["id"], price=250, qty=4)
    deleted = await client.delete(
        f"/leads/{lead['id']}/items/{item['id']}",
        headers=auth_headers,
    )
    assert deleted.status_code == 204

    summary = await client.get(f"/leads/{lead['id']}/items", headers=auth_headers)
    assert summary.json()["items"] == []
    assert summary.json()["total_amount"] == 0


@pytest.mark.asyncio
async def test_item_must_belong_to_lead(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
    order_item_factory,
) -> None:
    first = await lead_factory(name="Первая")
    second = await lead_factory(name="Вторая")
    item = await order_item_factory(first["id"])
    response = await client.patch(
        f"/leads/{second['id']}/items/{item['id']}",
        headers=auth_headers,
        json={"qty": 2},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"qty": 0}, "qty"),
        ({"price": -1}, "price"),
    ],
)
async def test_item_validation_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
    order_item_factory,
    payload: dict[str, int],
    field: str,
) -> None:
    lead = await lead_factory()
    item = await order_item_factory(lead["id"])
    response = await client.patch(
        f"/leads/{lead['id']}/items/{item['id']}",
        headers=auth_headers,
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == field
