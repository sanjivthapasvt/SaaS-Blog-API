import pytest
from httpx import AsyncClient

from tests.auth_utils import _create_user, _login_user

valid_users = []


@pytest.mark.asyncio
async def test_follow_yourself(client: AsyncClient):
    headers = await _create_user(client, "testuser1")
    resp = await client.get("/api/users/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    user_id = data["id"]
    valid_users.append(user_id)
    resp2 = await client.post(f"/api/users/{user_id}/follow", headers=headers)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_follow_non_existent_user(client: AsyncClient):
    headers = await _login_user(client, "testuser1")
    resp = await client.post(f"/api/users/21312312312312312/follow", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_follow_valid_user(client: AsyncClient):
    headers = await _create_user(client, "testuser2")
    resp = await client.post(f"/api/users/{valid_users[0]}/follow", headers=headers)
    resp2 = await client.get("/api/users/me", headers=headers)
    data = resp2.json()
    user_id = data["id"]
    valid_users.append(user_id)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_notificaion_on_follow_user(client: AsyncClient):
    headers = await _login_user(client, "testuser1")
    resp = await client.get("/api/notifications", headers=headers)
    data = resp.json()
    assert resp.status_code == 200

    # assert top-level keys
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "data" in data

    # assert data is list
    assert isinstance(data["data"], list)

    # if there is at least one notification, check its fields
    if data["data"]:
        notification = data["data"][0]
        assert "id" in notification
        assert "notification_type" in notification
        assert "message" in notification
        assert "triggered_by_user_id" in notification
        assert "created_at" in notification
        assert "blog_id" in notification


@pytest.mark.asyncio
async def test_follow_valid_user_multiple_times(client: AsyncClient):
    headers = await _login_user(client, "testuser2")
    resp = await client.post(f"/api/users/{valid_users[0]}/follow", headers=headers)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_unfollow_non_existent_user(client: AsyncClient):
    headers = await _login_user(client, "testuser2")
    resp = await client.delete("/api/users/1234134/follow", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unfollow_yourself(client: AsyncClient):
    headers = await _login_user(client, "testuser2")
    resp = await client.get("/api/users/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    user_id = data["id"]
    valid_users.append(user_id)
    resp2 = await client.delete(f"/api/users/{user_id}/follow", headers=headers)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_unfollow_valid_user(client: AsyncClient):
    headers = await _login_user(client, "testuser2")
    resp = await client.delete(f"/api/users/{valid_users[0]}/follow", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_follow_valid_user_after_unfollow(client: AsyncClient):
    headers = await _login_user(client, "testuser2")
    resp = await client.post(f"/api/users/{valid_users[0]}/follow", headers=headers)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_no_repeat_notification_on_follow__for_same_user(client: AsyncClient):
    headers = await _login_user(client, "testuser1")
    resp = await client.get("/api/notifications", headers=headers)
    data = resp.json()
    assert resp.status_code == 200
    assert len(data["data"]) < 2
