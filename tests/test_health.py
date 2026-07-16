async def test_health(client):
    """/health отвечает 200 и status=ok (БД не требуется)."""
    response = await client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["version"]
