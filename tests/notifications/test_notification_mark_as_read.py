import pytest
from httpx import AsyncClient

from tests.utils.auth_utils import _create_user


class TestNotificationMarkAsRead:
    """Test marking notifications as read"""

    @pytest.mark.asyncio
    async def test_mark_notification_as_read_success(self, client: AsyncClient):
        """Test successfully marking a notification as read"""
        author_headers = await _create_user(client, "ReadNotificationAuthor")
        liker_headers = await _create_user(client, "ReadNotificationLiker")

        # Create blog and like it to generate notification
        create_resp = await client.post(
            "/api/blogs",
            data={"title": "Mark Read Test", "content": "Test marking as read"},
            headers=author_headers,
        )
        assert create_resp.status_code == 201

        blogs_resp = await client.get("/api/blogs?search=Mark%Read")
        blog_id = blogs_resp.json()["data"][0]["id"]

        await client.post(f"/api/blogs/{blog_id}/like", headers=liker_headers)

        # Get notification ID
        notif_resp = await client.get("/api/notifications", headers=author_headers)
        notification_id = notif_resp.json()["data"][0]["id"]

        # Mark as read
        mark_read_resp = await client.post(
            f"/api/notifications/{notification_id}/mark_as_read", headers=author_headers
        )
        assert mark_read_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_mark_nonexistent_notification_as_read(self, client: AsyncClient):
        """Test marking non-existent notification as read"""
        headers = await _create_user(client, "NonExistentNotificationUser")

        mark_read_resp = await client.post(
            "/api/notifications/99999/mark_as_read", headers=headers
        )
        assert mark_read_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_mark_other_user_notification_as_read(self, client: AsyncClient):
        """Test that users cannot mark other users' notifications as read"""
        user1_headers = await _create_user(client, "NotificationUser1")
        user2_headers = await _create_user(client, "NotificationUser2")
        user3_headers = await _create_user(client, "NotificationUser3")

        # User1 creates blog, User2 likes it (creates notification for User1)
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Other User Notification",
                "content": "Test unauthorized read",
            },
            headers=user1_headers,
        )
        assert create_resp.status_code == 201

        blogs_resp = await client.get("/api/blogs?search=Other%User")
        blog_id = blogs_resp.json()["data"][0]["id"]

        await client.post(f"/api/blogs/{blog_id}/like", headers=user2_headers)

        # Get notification ID (User1's notification)
        notif_resp = await client.get("/api/notifications", headers=user1_headers)
        notification_id = notif_resp.json()["data"][0]["id"]

        # User3 tries to mark User1's notification as read
        mark_read_resp = await client.post(
            f"/api/notifications/{notification_id}/mark_as_read", headers=user3_headers
        )
        assert mark_read_resp.status_code == 403

    @pytest.mark.asyncio
    async def test_mark_as_read_unauthorized(self, client: AsyncClient):
        """Test marking notification as read without authentication"""
        mark_read_resp = await client.post("/api/notifications/1/mark_as_read")
        assert mark_read_resp.status_code == 401
