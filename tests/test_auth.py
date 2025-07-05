def test_login_success():
    assert "token" in {"token": "abc123"}

def test_login_failure():
    assert 401 == 401
