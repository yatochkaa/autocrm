from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_paginated_leads_response(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
) -> None:
    await lead_factory(name="Первая", priority="high")
    await lead_factory(name="Вторая", priority="normal")
    response = await client.get(
        "/leads",
        headers=auth_headers,
        params={"page": 1, "limit": 20, "include_completed": True},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert body["page"] == 1


@pytest.mark.asyncio
async def test_lost_status_requires_reason(
    client: AsyncClient,
    auth_headers: dict[str, str],
    lead_factory,
) -> None:
    lead = await lead_factory()
    for target in ("in_progress", "selection", "invoice"):
        moved = await client.patch(
            f"/leads/{lead['id']}/status",
            headers=auth_headers,
            json={"status": target},
        )
        assert moved.status_code == 200, moved.text

    rejected = await client.patch(
        f"/leads/{lead['id']}/status",
        headers=auth_headers,
        json={"status": "lost"},
    )
    assert rejected.status_code == 422

    accepted = await client.patch(
        f"/leads/{lead['id']}/status",
        headers=auth_headers,
        json={"status": "lost", "rejection_reason": "Цена"},
    )
    assert accepted.status_code == 200
    assert accepted.json()["rejection_reason"] == "Цена"
