import pytest


@pytest.fixture
def sample_payload() -> dict:
    return {
        "customer_name": "Иван",
        "part_query": "Тормозные колодки Lada Vesta",
        "source": "telegram",
    }


async def test_create_and_get_lead(client, sample_payload):
    """Создание заявки: статус NEW, маржа пустая."""
    r = await client.post("/leads", json=sample_payload)
    assert r.status_code == 201, r.text
    lead = r.json()
    assert lead["id"]
    assert lead["status"] == "new"
    assert lead["source"] == "telegram"
    assert lead["margin"] is None

    got = await client.get(f"/leads/{lead['id']}")
    assert got.status_code == 200
    assert got.json()["customer_name"] == "Иван"


async def test_list_leads(client, sample_payload):
    await client.post("/leads", json=sample_payload)
    await client.post("/leads", json={**sample_payload, "customer_name": "Пётр"})
    r = await client.get("/leads")
    assert r.status_code == 200
    assert len(r.json()) == 2


async def test_status_flow_and_margin(client, sample_payload):
    """Полный путь по воронке до Продажи + расчёт маржи."""
    r = await client.post(
        "/leads",
        json={**sample_payload, "sale_amount": 1500, "cost_amount": 900},
    )
    lead_id = r.json()["id"]
    for st in ["in_progress", "selection", "invoice", "won"]:
        rr = await client.post(f"/leads/{lead_id}/status", json={"status": st})
        assert rr.status_code == 200, rr.text
    body = rr.json()
    assert body["status"] == "won"
    assert body["margin"] == 600


async def test_invalid_transition(client, sample_payload):
    """Прыжок NEW → WON запрещён."""
    r = await client.post("/leads", json=sample_payload)
    lead_id = r.json()["id"]
    rr = await client.post(f"/leads/{lead_id}/status", json={"status": "won"})
    assert rr.status_code == 409


async def test_won_requires_sale_amount(client, sample_payload):
    """Дойти до INVOICE без суммы и не смочь закрыть в WON."""
    r = await client.post("/leads", json=sample_payload)
    lead_id = r.json()["id"]
    for st in ["in_progress", "selection", "invoice"]:
        ok = await client.post(f"/leads/{lead_id}/status", json={"status": st})
        assert ok.status_code == 200, ok.text
    rr = await client.post(f"/leads/{lead_id}/status", json={"status": "won"})
    assert rr.status_code == 409
