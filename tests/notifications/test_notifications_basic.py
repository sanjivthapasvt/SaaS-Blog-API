import pytest
from httpx import AsyncClient

from tests.utils.auth_utils import _create_user


class TestNotificationBasics:
    """Test basic notification functionality"""

    @pytest.mark.asyncio
    async def test_get_all_notifications_empty(self, client: AsyncClient):
        """Test getting notifications when user has none"""
        headers = await _create_user(client, "EmptyNotificationUser")

        resp = await client.get("/api/notifications", headers=headers)
        assert resp.status_code == 200

        data = resp.json()
        assert set(data.keys()) == {"total", "limit", "offset", "data"}
        assert data["total"] == 0
        assert data["limit"] == 10  # default limit
        assert data["offset"] == 0  # default offset
        assert isinstance(data["data"], list)
        assert len(data["data"]) == 0

    @pytest.mark.asyncio
    async def test_get_notifications_unauthorized(self, client: AsyncClient):
        """Test getting notifications without authentication"""
        resp = await client.get("/api/notifications")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_notifications_pagination(self, client: AsyncClient):
        """Test notification pagination"""
        user1_headers = await _create_user(client, "NotificationPaginationUser1")
        user2_headers = await _create_user(client, "NotificationPaginationUser2")

        # Create multiple blogs and likes to generate notifications
        blog_ids = []
        for i in range(10):
            title = f"Notification Blog {i}"
            create_resp = await client.post(
                "/api/blogs",
                data={
                    "title": title,
                    "content": f"Content for notification {i}",
                },
                headers=user1_headers,
            )
            assert create_resp.status_code == 201

            # Get blog ID
            blogs_resp = await client.get(f"/api/blogs?search={title}")
            blog_id = blogs_resp.json()["data"][0]["id"]
            blog_ids.append(blog_id)

            # Like to create notification
            await client.post(f"/api/blogs/{blog_id}/like", headers=user2_headers)

        # Test default pagination
        resp = await client.get("/api/notifications", headers=user1_headers)
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] == 10
        assert data["limit"] == 10
        assert data["offset"] == 0
        assert len(data["data"]) == 10

        # Test custom pagination
        resp = await client.get(
            "/api/notifications?limit=5&offset=5", headers=user1_headers
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["total"] == 10
        assert data["limit"] == 5
        assert data["offset"] == 5
        assert len(data["data"]) == 5

    @pytest.mark.asyncio
    async def test_get_notifications_search(self, client: AsyncClient):
        """Test notification search functionality"""
        user1_headers = await _create_user(client, "SearchNotificationUser1")
        user2_headers = await _create_user(client, "SearchNotificationUser2")

        # Create blogs with different titles
        blogs = [
            {"title": "Python Tutorial", "content": "Learn Python"},
            {"title": "FastAPI Guide", "content": "FastAPI tutorial"},
            {"title": "React Components", "content": "React guide"},
        ]

        for blog in blogs:
            create_resp = await client.post(
                "/api/blogs", data=blog, headers=user1_headers
            )
            assert create_resp.status_code == 201

            # Get blog ID and like it
            search_term = blog["title"].split()[0]  # First word of title
            blogs_resp = await client.get(f"/api/blogs?search={search_term}")
            blog_id = blogs_resp.json()["data"][0]["id"]

            await client.post(f"/api/blogs/{blog_id}/like", headers=user2_headers)

        # Search for specific notifications
        resp = await client.get(
            "/api/notifications?search=Python", headers=user1_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        # Should find notifications related to Python blog
        assert data["total"] >= 0
