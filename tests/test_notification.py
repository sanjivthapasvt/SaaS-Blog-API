import pytest
from httpx import AsyncClient
from tests.auth_utils import _create_user, _login_user


@pytest.mark.asyncio
async def test_get_all_notifications_empty(client: AsyncClient):
    header = await _create_user(client, "test_user3")
    resp = await client.get("/api/notifications", headers=header)
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"total", "limit", "offset", "data"}
    assert data["total"] == 0
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_like_blogs_to_create_notification_and_get_notification(
    client: AsyncClient,
):
    headers1 = await _create_user(client, "testuser4")
    headers2 = await _create_user(client, "testuser5")

    # create a blog
    resp = await client.post(
        "/api/blogs",
        data={
            "title": "Likeme",
            "content": "Please like me",
        },
        headers=headers1,
    )
    assert resp.status_code == 201

    # fetch id (search by title)
    resp2 = await client.get("/api/blogs", params={"search": "Likeme"})
    assert resp2.status_code == 200
    items = resp2.json()["data"]
    assert items and items[0]["title"] == "Likeme"
    blog_id = items[0]["id"]

    # like
    resp3 = await client.post(f"/api/blogs/{blog_id}/like", headers=headers2)
    assert resp3.status_code == 200
    assert "added" in resp3.json()["detail"]

    # unlike blog
    resp5 = await client.post(f"/api/blogs/{blog_id}/like", headers=headers2)
    assert resp5.status_code == 200
    assert "removed" in resp5.json()["detail"]

    # like again to check the same blog doesn't create multiple notification
    resp3 = await client.post(f"/api/blogs/{blog_id}/like", headers=headers2)
    assert resp3.status_code == 200
    assert "added" in resp3.json()["detail"]

    # test for get notification
    resp = await client.get("/api/notifications", headers=headers1)
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"total", "limit", "offset", "data"}
    assert data["total"] == 1
    assert isinstance(data["data"], list)

