from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.auth_utils import _create_user, _login_user

async def _auth_header(client: AsyncClient) -> dict[str, str]:
    unique = uuid4().hex[:8]
    reg = await client.post(
        "/auth/register",
        json={
            "username": f"blogger_{unique}",
            "first_name": "Blog",
            "last_name": "Ger",
            "email": f"blogger_{unique}@example.com",
            "password": "secret123",
        },
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_all_blogs_empty(client: AsyncClient):
    resp = await client.get("/api/blogs")
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"total", "limit", "offset", "data"}
    assert data["total"] == 0
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_create_and_fetch_blog_flow(client: AsyncClient):
    headers = await _auth_header(client)

    # create blog
    resp = await client.post(
        "/api/blogs",
        data={
            "title": "First Post",
            "content": "Hello World",
            "tags": "#fastapi#sqlmodel",
        },
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["detail"].startswith("Successfully")

    # list blogs
    resp2 = await client.get("/api/blogs")
    assert resp2.status_code == 200
    page = resp2.json()
    assert page["total"] == 1
    assert page["data"][0]["title"] == "First Post"
    blog_id = page["data"][0]["id"]

    # get by id
    resp3 = await client.get(f"/api/blogs/{blog_id}")
    assert resp3.status_code == 200
    blog = resp3.json()
    assert blog["id"] == blog_id


@pytest.mark.asyncio
async def test_like_unlike_and_liked_blogs(client: AsyncClient):
    headers = await _auth_header(client)

    # create a blog
    resp = await client.post(
        "/api/blogs",
        data={
            "title": "Likeable",
            "content": "Please like me",
        },
        headers=headers,
    )
    assert resp.status_code == 201

    # fetch id (search by title)
    resp2 = await client.get("/api/blogs", params={"search": "Likeable"})
    assert resp2.status_code == 200
    items = resp2.json()["data"]
    assert items and items[0]["title"] == "Likeable"
    blog_id = items[0]["id"]

    # like
    resp3 = await client.post(f"/api/blogs/{blog_id}/like", headers=headers)
    assert resp3.status_code == 200
    assert "added" in resp3.json()["detail"]

    # list liked blogs
    resp4 = await client.get("/api/blogs/liked", headers=headers)
    assert resp4.status_code == 200
    liked = resp4.json()
    assert liked["total"] >= 1
    assert any(item["id"] == blog_id for item in liked["data"])

    # unlike blog
    resp5 = await client.post(f"/api/blogs/{blog_id}/like", headers=headers)
    assert resp5.status_code == 200
    assert "removed" in resp5.json()["detail"]

    # list liked blogs after unlike
    resp6 = await client.get("/api/blogs/liked", headers=headers)
    assert resp6.status_code == 200
    liked = resp6.json()
    assert liked["total"] == 0

@pytest.mark.asyncio
async def test_get_liked_blogs(client: AsyncClient):
    headers = await _auth_header(client)

    resp = await client.post(
        "/api/blogs",
        data={
            "title": "Hope you get notification",
            "content": "This is test for getting notification sheesh",
        },
        headers=headers,
    )
    res = await client.post("/api/blogs/1/like", headers=headers)
    assert res.status_code == 200
    
    resp = await client.get("/api/blogs/liked", headers=headers)
    assert resp.status_code == 200
    
    data = resp.json()
    assert set(data.keys()) == {"total", "limit", "offset", "data"}
    assert data["total"] == 1
    assert isinstance(data["data"], list)
    assert set(data["data"][0].keys()) == {"id", "title", "thumbnail_url", "author", "tags", "created_at"}

@pytest.mark.asyncio
async def test_delete_blog(client: AsyncClient):
    await _create_user(client, "test_delete_blog_user")
    headers =  await _login_user(client, "test_delete_blog_user")

    resp = await client.post(
        "/api/blogs",
        data={
            "title": "Delete blog test",
            "content": "This is test for getting notification sheesh",
        },
        headers=headers,
    )
    assert resp.status_code == 201
    
    get_resp = await client.get("/api/blogs?search=Delete%blog%test")
    get_data = get_resp.json()["data"]
    blog_id = get_data[0]["id"]
    
    del_resp = await client.delete(f"/api/blogs/{blog_id}", headers=headers)
    assert del_resp.status_code == 200

@pytest.mark.asyncio
async def test_update_blog(client: AsyncClient):
    headers =  await _login_user(client, "test_delete_blog_user")

    resp = await client.post(
        "/api/blogs",
        data={
            "title": "This is to be updated",
            "content": "This is test for updating blog",
        },
        headers=headers,
    )
    
    assert resp.status_code == 201
    
    get_resp = await client.get("/api/blogs?search=updated")
    get_data = get_resp.json()["data"]
    blog_id = get_data[0]["id"]
    
    with open("tests/test1.png", "rb") as f:
        data = {
            "title": "the blog that needs to be updated has been updated",
            "content": "you are seeing the blog that has been updated"
        }
        files = {"thumbnail": ("first.png", f, "image/png")}
        update_resp = await client.patch(f"/api/blogs/{blog_id}",data=data,files=files, headers=headers)
        assert update_resp.status_code == 200
    
    updated_resp = await client.get(f"/api/blogs/{blog_id}")
    assert updated_resp.status_code == 200
    
    updated_data = updated_resp.json()

    assert updated_data["title"] == "the blog that needs to be updated has been updated"
    assert updated_data["content"] == "you are seeing the blog that has been updated"