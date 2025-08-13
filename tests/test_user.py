import pytest


@pytest.mark.asyncio
async def test_register_and_login_flow(client):
    register_payload = {
        "username": "testuser",
        "first_name": "test",
        "last_name": "user",
        "email": "testuser@example.com",
        "password": "secret123",
    }

    resp = await client.post("/auth/register", json=register_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert set(data.keys()) == {"access_token", "token_type"}
    assert data["token_type"] == "bearer"

    login_payload = {"username": "testuser", "password": "secret123"}
    resp = await client.post("/auth/login", json=login_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert set(data.keys()) == {"access_token", "token_type"}
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_register_duplicate_username_email(client):
    payload_duplicate_username = {
        "username": "testuser",
        "first_name": "test",
        "last_name": "user",
        "email": "testuser@example.com",
        "password": "secret123",
    }
    payload_duplicate_email = {
        "username": "testuser1",
        "first_name": "test",
        "last_name": "user",
        "email": "testuser@example.com",
        "password": "secret123",
    }
    resp1 = await client.post("/auth/register", json=payload_duplicate_username)
    assert resp1.status_code == 400

    resp2 = await client.post("/auth/register", json=payload_duplicate_email)
    assert resp2.status_code == 400
    assert "exists" in resp2.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_wrong_password(client):
    payload = {
        "username": "testuser5",
        "password": "secret123",
    }
    resp = await client.post("/auth/login", json=payload)
    assert resp.status_code == 400

    bad_login = {"username": "testuser", "password": "secret1234"}
    resp2 = await client.post("/auth/login", json=bad_login)
    assert resp2.status_code == 400
    assert "incorrect" in resp2.json()["detail"].lower()


