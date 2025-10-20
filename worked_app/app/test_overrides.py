from fastapi.testclient import TestClient
from main import app


def get_db():
    return "REAL_DB"


def fake_db():
    return "FAKE_DB"


app.dependency_overrides[get_db] = fake_db

client = TestClient(app)


def test_whoami_uses_fake_db():
    r = client.get("/whoami")
    assert r.status_code == 200
    assert r.json() == {"db": "FAKE_DB"}


def test_bad_token():
    r = client.get("/items/foo", headers={"X-Token": "wrong"})
    assert r.status_code == 400
    assert r.json() == {"detail": "Invalid X-Token header"}
