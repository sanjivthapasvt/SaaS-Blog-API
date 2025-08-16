import pytest
import asyncio
from tests.auth_utils import _create_user, _login_user
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_new_blog_notification_to_follower(client: AsyncClient):
    await _create_user(client, "test_user_notification1")    
    await _create_user(client, "test_user_notification2")    
    await _create_user(client, "test_user_notification3")    
    
    user1_header = await _login_user(client, "test_user_notification1")
    user2_header = await _login_user(client, "test_user_notification2")    
    user3_header = await _login_user(client, "test_user_notification3")    
    
    user2 = await client.get("/api/users/me", headers=user2_header)
    assert user2.status_code == 200
    user2_data = user2.json()
    user2_id = user2_data["id"]
    
    res1 = await client.post(f"/api/users/{user2_id}/follow", headers=user1_header)
    assert res1.status_code == 200
    
    res2 = await client.post(f"/api/users/{user2_id}/follow", headers=user3_header)
    assert res2.status_code == 200
    
    resp = await client.post(
        "/api/blogs",
        data={
            "title": "Hope you get notification",
            "content": "This is test for getting notification sheesh"
        },
        headers=user2_header
    )
    
    assert resp.status_code == 201


    user1_resp = await client.get(f"/api/notifications", headers=user1_header)
    assert user1_resp.status_code == 200
    user1_data = user1_resp.json()
    assert set(user1_data.keys()) == {"total", "limit", "offset", "data"}
    assert user1_data["total"] == 1
    assert isinstance(user1_data["data"], list)


    user4_resp = await client.get(f"/api/notifications", headers=user3_header)
    assert user4_resp.status_code == 200
    user4_data = user4_resp.json()
    assert set(user4_data.keys()) == {"total", "limit", "offset", "data"}
    assert user4_data["total"] == 1
    assert isinstance(user4_data["data"], list)
    