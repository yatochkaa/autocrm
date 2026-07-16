from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    credentials = {"email": "analytics-manager@example.com", "password": "password123"}
    registered = await client.post("/auth/register", json=credentials)
    assert registered.status_code == 201, registered.text
    logged_in = await client.post("/auth/login", json=credentials)
    assert logged_in.status_code == 200, logged_in.text
    return {"Authorization": f"Bearer {logged_in.json()['access_token']}"}


async def create_lead(
    client: AsyncClient,
    headers: dict[str, str],
    source: str,
) -> int:
    response = await client.post(
        "/leads",
        headers=headers,
        json={"name": f"Lead {source}", "source": source},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def add_item_and_win(
    client: AsyncClient,
    headers: dict[str, str],
    lead_id: int,
    price: float,
    qty: int,
) -> None:
    item = await client.post(
        f"/leads/{lead_id}/items",
        headers=headers,
        json={"name": "Деталь", "price": price, "qty": qty},
    )
    assert item.status_code == 201, item.text
    for target in ("in_progress", "selection", "invoice", "won"):
        changed = await client.patch(
            f"/leads/{lead_id}/status",
            headers=headers,
            json={"status": target},
        )
        assert changed.status_code == 200, changed.text


async def analytics_dataset(
    client: AsyncClient,
    headers: dict[str, str],
) -> None:
    telegram = await create_lead(client, headers, "telegram")
    manual = await create_lead(client, headers, "manual")
    await create_lead(client, headers, "site")
    await add_item_and_win(client, headers, telegram, price=1000, qty=2)
    await add_item_and_win(client, headers, manual, price=500, qty=3)


def period_query() -> str:
    today = date.today().isoformat()
    return f"date_from={today}&date_to={today}"


@pytest.mark.asyncio
async def test_overview_conversion_revenue_and_average_check(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    await analytics_dataset(client, headers)

    response = await client.get(
        f"/analytics/overview?{period_query()}",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_leads"] == 3
    assert body["sales"] == 2
    assert body["conversion_percent"] == 66.67
    assert body["revenue"] == 3500
    assert body["average_check"] == 1750


@pytest.mark.asyncio
async def test_sources_are_ready_for_chart(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    await analytics_dataset(client, headers)

    response = await client.get(
        f"/analytics/sources?{period_query()}",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["labels"] == ["telegram", "manual", "site"]
    assert body["values"] == [1, 1, 1]
    assert sum(item["share_percent"] for item in body["items"]) == pytest.approx(
        100,
        abs=0.02,
    )


@pytest.mark.asyncio
async def test_top_managers_by_sales(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    await analytics_dataset(client, headers)

    response = await client.get(
        f"/analytics/managers?{period_query()}&limit=10",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["email"] == "analytics-manager@example.com"
    assert body["items"][0]["sales"] == 2
    assert body["items"][0]["revenue"] == 3500
    assert body["sales_values"] == [2]


@pytest.mark.asyncio
async def test_average_stage_times_from_history(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    lead_id = await create_lead(client, headers, "telegram")
    await add_item_and_win(client, headers, lead_id, price=100, qty=1)

    response = await client.get(
        f"/analytics/stage-times?{period_query()}",
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["labels"] == ["new", "in_progress", "selection", "invoice"]
    assert [item["sample_count"] for item in body["items"]] == [1, 1, 1, 1]
    assert all(value >= 0 for value in body["values_hours"])


@pytest.mark.asyncio
async def test_invalid_analytics_period_returns_422(client: AsyncClient) -> None:
    headers = await auth_headers(client)
    tomorrow = date.today() + timedelta(days=1)
    response = await client.get(
        "/analytics/overview",
        headers=headers,
        params={
            "date_from": tomorrow.isoformat(),
            "date_to": date.today().isoformat(),
        },
    )
    assert response.status_code == 422
    assert "date_from" in response.json()["detail"]
