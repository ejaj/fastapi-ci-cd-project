from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_queue_email_ok():
    r = client.post("/api/notifications/send", params={"email": "a@b.com"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "queued"
    assert data["to"] == "a@b.com"
