from uuid import uuid4

from fastapi.testclient import TestClient

from api.main import app, table, HOTEL

client = TestClient(app)


def test_dynamodb_request_lifecycle():
    guest = f"Demo {uuid4().hex[:8]}"
    created = client.post("/api/requests", json={
        "guest": guest, "service": "Airport transfer", "arrival": "2026-11-04", "note": "Test only"
    })
    assert created.status_code == 201
    item = created.json()
    try:
        assert item["version"] == 1 and item["status"] == "new"
        assert any(row["request_id"] == item["request_id"] for row in client.get("/api/requests?status=new").json())
        updated = client.patch(f"/api/requests/{item['request_id']}", json={"status": "contacted", "version": 1})
        assert updated.status_code == 200
        assert updated.json()["version"] == 2
        assert updated.json()["hotel_status"] == "mirador-azul#contacted"
        assert client.patch(f"/api/requests/{item['request_id']}", json={"status": "closed", "version": 1}).status_code == 409
        assert client.post("/api/requests", json={"guest": guest, "service": "Spa", "arrival": "2026-02-30"}).status_code == 422
        assert client.post("/api/requests", json={"guest": "  ", "service": "Spa", "arrival": "2026-11-04"}).status_code == 422
    finally:
        table().delete_item(Key={"hotel_id": HOTEL, "request_id": item["request_id"]})
