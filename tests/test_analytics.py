from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


async def move_to_won(
    client: AsyncClient,
    headers: dict[str, str],
    lead_id: int,
) -> None:
    for status in ("in_progress", "selection", "invoice", "won"):
        response = await client.patch(
            f"/leads/{lead_id}/status",
            headers=headers,
            json={"status": status},
        )
        assert response.status_code == 200, response.text


async def create_analytics_dataset(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
    order_item_factory,
) -> None:
    telegram = await lead_factory(name="Telegram", source="telegram")
    manual = await lead_factory(name="Manual", source="manual")
    await lead_factory(name="Site", source="site")

    await order_item_factory(telegram["id"], price=1000, qty=2)
    await order_item_factory(manual["id"], price=500, qty=3)
    await move_to_won(client, auth_headers, telegram["id"])
    await move_to_won(client, auth_headers, manual["id"])


def period_params() -> dict[str, str]:
    today = date.today().isoformat()
    return {"date_from": today, "date_to": today}


@pytest.mark.asyncio
async def test_overview_conversion_revenue_and_average_check(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
    order_item_factory,
) -> None:
    await create_analytics_dataset(
        client,
        auth_headers,
        lead_factory,
        order_item_factory,
    )
    response = await client.get(
        "/analytics/overview",
        headers=auth_headers,
        params=period_params(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_leads"] == 3
    assert body["sales"] == 2
    assert body["conversion_percent"] == 66.67
    assert body["revenue"] == 3500
    assert body["average_check"] == 1750


@pytest.mark.asyncio
async def test_sources_are_ready_for_chart(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
    order_item_factory,
) -> None:
    await create_analytics_dataset(
        client,
        auth_headers,
        lead_factory,
        order_item_factory,
    )
    response = await client.get(
        "/analytics/sources",
        headers=auth_headers,
        params=period_params(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["labels"] == ["telegram", "manual", "site"]
    assert body["values"] == [1, 1, 1]
    assert sum(item["share_percent"] for item in body["items"]) == pytest.approx(
        100,
        abs=0.02,
    )


@pytest.mark.asyncio
async def test_top_managers_by_sales(
    client: AsyncClient,
    auth_user: dict[str, object],
    lead_factory,
    order_item_factory,
) -> None:
    headers = auth_user["headers"]
    await create_analytics_dataset(client, headers, lead_factory, order_item_factory)
    response = await client.get(
        "/analytics/managers",
        headers=headers,
        params={**period_params(), "limit": 10},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["manager_id"] == auth_user["id"]
    assert body["items"][0]["sales"] == 2
    assert body["items"][0]["revenue"] == 3500
    assert body["sales_values"] == [2]


@pytest.mark.asyncio
async def test_average_stage_times_from_history(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
) -> None:
    lead = await lead_factory(source="telegram")
    await move_to_won(client, auth_headers, lead["id"])
    response = await client.get(
        "/analytics/stage-times",
        headers=auth_headers,
        params=period_params(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["labels"] == ["new", "in_progress", "selection", "invoice"]
    assert [item["sample_count"] for item in body["items"]] == [1, 1, 1, 1]
    assert all(value >= 0 for value in body["values_hours"])


@pytest.mark.asyncio
async def test_dashboard_combines_chart_blocks(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
    order_item_factory,
) -> None:
    await create_analytics_dataset(
        client,
        auth_headers,
        lead_factory,
        order_item_factory,
    )
    response = await client.get(
        "/analytics/dashboard",
        headers=auth_headers,
        params={**period_params(), "manager_limit": 5},
    )
    assert response.status_code == 200
    assert set(response.json()) == {
        "overview",
        "sources",
        "managers",
        "stage_times",
    }


@pytest.mark.asyncio
async def test_invalid_analytics_period_returns_422(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    response = await client.get(
        "/analytics/overview",
        headers=auth_headers,
        params={
            "date_from": (date.today() + timedelta(days=1)).isoformat(),
            "date_to": date.today().isoformat(),
        },
    )
    assert response.status_code == 422
    assert "date_from" in response.json()["detail"]
