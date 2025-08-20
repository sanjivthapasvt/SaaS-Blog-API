from uuid import uuid4

from httpx import AsyncClient


async def _create_user(client: AsyncClient, username: str) -> dict[str, str]:
    reg = await client.post(
        "/api/auth/register",
        json={
            "username": f"{username}",
            "first_name": "Blog",
            "last_name": "Ger",
            "email": f"{username}@example.com",
            "password": "SecretPassword1#",
        },
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _login_user(client: AsyncClient, username: str) -> dict[str, str]:
    log = await client.post(
        "/api/auth/login",
        json={
            "username": f"{username}",
            "password": "SecretPassword1#",
        },
    )
    assert log.status_code == 200, log.text
    token = log.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_test_user(client: AsyncClient, suffix: str = None) -> tuple[dict[str, str], dict]:  # type: ignore
    """helper to create a test user and return headers + user data"""
    unique = uuid4().hex[:8] if not suffix else suffix
    user_data = {
        "username": f"testuser_{unique}",
        "first_name": "Test",
        "last_name": "User",
        "email": f"testuser_{unique}@example.com",
        "password": "Secret123@",
    }

    resp = await client.post("/api/auth/register", json=user_data)
    assert resp.status_code == 200

    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    return headers, user_data
