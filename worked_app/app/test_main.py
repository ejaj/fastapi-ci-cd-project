from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_read_main():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json() == {"msg": "Hello World"}
