import pytest
from httpx import AsyncClient

from tests.auth_utils import _create_user


class TestFollowNotifications:
    """Test notifications for follow/unfollow actions"""

    @pytest.mark.asyncio
    async def test_new_blog_notifies_followers(self, client: AsyncClient):
        """Test that creating a blog notifies all followers"""
        author_headers = await _create_user(client, "NotificationAuthor")
        follower1_headers = await _create_user(client, "Follower1")
        follower2_headers = await _create_user(client, "Follower2")
        non_follower_headers = await _create_user(client, "NonFollower")

        # Get author ID
        author_resp = await client.get("/api/users/me", headers=author_headers)
        author_id = author_resp.json()["id"]

        # Followers follow the author
        await client.post(f"/api/users/{author_id}/follow", headers=follower1_headers)
        await client.post(f"/api/users/{author_id}/follow", headers=follower2_headers)

        # Author creates a blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Follower Notification Blog",
                "content": "This should notify followers",
            },
            headers=author_headers,
        )
        assert create_resp.status_code == 201

        # Check follower1 notifications
        notif1_resp = await client.get("/api/notifications", headers=follower1_headers)
        assert notif1_resp.status_code == 200
        data1 = notif1_resp.json()
        assert data1["total"] == 1

        # Check follower2 notifications
        notif2_resp = await client.get("/api/notifications", headers=follower2_headers)
        assert notif2_resp.status_code == 200
        data2 = notif2_resp.json()
        assert data2["total"] == 1

        # Check non-follower (should have no notifications)
        notif3_resp = await client.get(
            "/api/notifications", headers=non_follower_headers
        )
        assert notif3_resp.status_code == 200
        data3 = notif3_resp.json()
        assert data3["total"] == 0

        # Verify notification content
        notification = data1["data"][0]
        assert notification["notification_type"] == "new_blog"
        assert notification["triggered_by_user_id"] == author_id

    @pytest.mark.asyncio
    async def test_unfollow_stops_blog_notifications(self, client: AsyncClient):
        """Test that unfollowing stops receiving blog notifications"""
        author_headers = await _create_user(client, "UnfollowAuthor")
        follower_headers = await _create_user(client, "UnfollowFollower")

        # Get author ID
        author_resp = await client.get("/api/users/me", headers=author_headers)
        author_id = author_resp.json()["id"]

        # Follow author
        await client.post(f"/api/users/{author_id}/follow", headers=follower_headers)

        # Author creates first blog
        await client.post(
            "/api/blogs",
            data={"title": "Before Unfollow", "content": "Should get notification"},
            headers=author_headers,
        )

        # Verify notification received
        notif_resp = await client.get("/api/notifications", headers=follower_headers)
        assert notif_resp.json()["total"] == 1

        # Unfollow
        await client.delete(f"/api/users/{author_id}/follow", headers=follower_headers)

        # Author creates second blog
        await client.post(
            "/api/blogs",
            data={"title": "After Unfollow", "content": "Should not get notification"},
            headers=author_headers,
        )

        # Should still have only one notification
        notif_resp2 = await client.get("/api/notifications", headers=follower_headers)
        assert notif_resp2.json()["total"] == 1
