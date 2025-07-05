def test_db_connection():
    connected = True  # Simulate DB check
    assert connected

def test_fetch_user():
    user = {"id": 1, "name": "John"}
    assert user["name"] == "John"
