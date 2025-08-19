from httpx import AsyncClient


async def _create_user(client: AsyncClient, username: str) -> dict[str, str]:
    reg = await client.post(
        "/auth/register",
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
        "/auth/login",
        json={
            "username": f"{username}",
            "password": "SecretPassword1#",
        },
    )
    assert log.status_code == 200, log.text
    token = log.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
