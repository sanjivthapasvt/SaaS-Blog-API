from uuid import uuid4

import pytest
from httpx import AsyncClient


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


