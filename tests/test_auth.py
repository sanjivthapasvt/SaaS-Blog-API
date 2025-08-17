import pytest
from httpx import AsyncClient

from tests.auth_utils import _create_user


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
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
    assert set(data.keys()) == {"access_token", "refresh_token", "token_type"}
    assert data["token_type"] == "bearer"

    login_payload = {"username": "testuser", "password": "secret123"}
    resp = await client.post("/auth/login", json=login_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert set(data.keys()) == {"access_token", "refresh_token", "token_type"}
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username_email(client: AsyncClient):
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
async def test_login_wrong_password(client: AsyncClient):
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


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    headers = await _create_user(client=client, username="test_user123")
    resp = await client.post("/auth/logout", headers=headers)
    data = resp.json()
    assert resp.status_code == 200
    assert "Logged out successfully" in data["detail"]


@pytest.mark.asyncio
async def test_logout_without_being_logged_in(client: AsyncClient):
    resp = await client.post("/auth/logout")
    data = resp.json()
    assert resp.status_code == 403
    assert "Not authenticated" in data["detail"]


@pytest.mark.asyncio
async def test_refresh_token_route(client: AsyncClient):
    payload = {
        "username": "testuser",
        "password": "secret123",
    }
    resp = await client.post("/auth/login", json=payload)
    data = resp.json()
    refresh_token = data["refresh_token"]

    assert resp.status_code == 200
    resp2 = await client.post(f"/auth/refresh?refresh_token={refresh_token}")

    assert resp2.status_code == 200
    data2 = resp2.json()

    assert set(data2.keys()) == {"access_token", "refresh_token", "token_type"}


@pytest.mark.asyncio
async def test_invalid_refresh_token_route(client: AsyncClient):
    payload = {
        "username": "testuser",
        "password": "secret123",
    }
    resp = await client.post("/auth/login", json=payload)
    data = resp.json()
    access_token = data["access_token"]

    assert resp.status_code == 200
    resp2 = await client.post(f"/auth/refresh?refresh_token={access_token}")

    assert resp2.status_code == 401
    data2 = resp2.json()

    assert "Invalid" in data2["detail"]
