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


async def _create_blog(client: AsyncClient):
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

    assert resp.status_code == 201

    # list blogs
    resp2 = await client.get("/api/users/me/blogs", headers=headers)
    assert resp2.status_code == 200
    page = resp2.json()
    blog_id = page["data"][0]["id"]

    return blog_id


@pytest.mark.asyncio
async def test_get_all_comments_from_blogs_empty(client: AsyncClient):
    blog_id = await _create_blog(client)

    resp = await client.get(f"/api/blogs/{blog_id}/comments")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_and_fetch_comment_flow(client: AsyncClient):
    headers = await _auth_header(client)
    blog_id = await _create_blog(client)

    # create comment on blog
    resp = await client.post(
        f"/api/blogs/{blog_id}/comments",
        json={"content": "This is a test comment"},
        headers=headers,
    )

    assert resp.status_code == 200

    # create comment on blog
    resp2 = await client.post(
        f"/api/blogs/{blog_id}/comments",
        json={"content": "This is a test comment 2"},
        headers=headers,
    )

    assert resp2.status_code == 200

    # get all comments
    resp3 = await client.get(f"/api/blogs/{blog_id}/comments")
    assert resp3.status_code == 200

    data = resp3.json()

    assert isinstance(data, list)
    comment_id = data[0]["id"]

    # update comment
    resp4 = await client.patch(
        f"/api/comments/{comment_id}",
        json={"content": "This is updated content"},
        headers=headers,
    )
    assert resp4.status_code == 200

    # delete comment
    resp5 = await client.delete(f"/api/comments/{comment_id}", headers=headers)
    assert resp5.status_code == 200
