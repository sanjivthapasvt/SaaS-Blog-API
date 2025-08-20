from uuid import uuid4

from httpx import AsyncClient

from tests.utils.auth_utils import _create_user


async def _create_blog(client: AsyncClient, headers=None) -> tuple[int, dict[str, str]]:
    """Create a blog and return blog_id and headers"""
    if headers is None:
        headers = await _create_user(client, f"UserCreateBlog{uuid4().hex[:6]}")

    resp = await client.post(
        "/api/blogs",
        data={
            "title": f"Test Blog {uuid4().hex[:6]}",
            "content": "Test blog content",
            "tags": "#test#blog",
        },
        headers=headers,
    )
    assert resp.status_code == 201

    # Get blog ID from user's blogs
    resp2 = await client.get("/api/users/me/blogs", headers=headers)
    assert resp2.status_code == 200
    page = resp2.json()
    blog_id = page["data"][0]["id"]

    return blog_id, headers
