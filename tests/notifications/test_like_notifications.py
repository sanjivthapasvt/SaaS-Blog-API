import pytest
from httpx import AsyncClient

from tests.auth_utils import _create_user



class TestLikeNotifications:
    """Test notifications for blog likes"""

    @pytest.mark.asyncio
    async def test_like_creates_notification(self, client: AsyncClient):
        """Test that liking a blog creates a notification for the author"""
        author_headers = await _create_user(client, "BlogAuthor")
        liker_headers = await _create_user(client, "BlogLiker")

        # Create a blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Likeable Blog",
                "content": "Please like this blog",
            },
            headers=author_headers,
        )
        assert create_resp.status_code == 201

        # Get blog ID
        blogs_resp = await client.get("/api/blogs?search=Likeable")
        blog_id = blogs_resp.json()["data"][0]["id"]

        # Like the blog
        like_resp = await client.post(f"/api/blogs/{blog_id}/like", headers=liker_headers)
        assert like_resp.status_code == 200

        # Check that author received notification
        notif_resp = await client.get("/api/notifications", headers=author_headers)
        assert notif_resp.status_code == 200
        
        data = notif_resp.json()
        assert data["total"] == 1
        
        notification = data["data"][0]
        assert notification["notification_type"] == "like" 
        assert notification["blog_id"] == blog_id
        assert "triggered_by_user_id" in notification

    @pytest.mark.asyncio
    async def test_unlike_removes_notification(self, client: AsyncClient):
        """Test that unliking removes the notification"""
        author_headers = await _create_user(client, "UnlikeAuthor")
        liker_headers = await _create_user(client, "UnlikeLiker")

        # Create blog
        create_resp = await client.post(
            "/api/blogs",
            data={"title": "Unlike Test Blog", "content": "Test unlike notification"},
            headers=author_headers,
        )
        assert create_resp.status_code == 201

        blogs_resp = await client.get("/api/blogs?search=Unlike%Test")
        blog_id = blogs_resp.json()["data"][0]["id"]

        # Like and then unlike
        await client.post(f"/api/blogs/{blog_id}/like", headers=liker_headers)  #Like 
        await client.post(f"/api/blogs/{blog_id}/like", headers=liker_headers)  # Unlike 

        # Check notifications - should be empty
        notif_resp = await client.get("/api/notifications", headers=author_headers)
        assert notif_resp.status_code == 200
        data = notif_resp.json()
        
        #Notificatoin should be empty
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_multiple_likes_same_user_single_notification(self, client: AsyncClient):
        """Test that multiple like/unlike don't create duplicate notifications"""
        author_headers = await _create_user(client, "MultiLikeAuthor")
        liker_headers = await _create_user(client, "MultiLiker")

        # Create blog
        create_resp = await client.post(
            "/api/blogs",
            data={"title": "Multi Like Test", "content": "Testing multiple likes"},
            headers=author_headers,
        )
        assert create_resp.status_code == 201

        blogs_resp = await client.get("/api/blogs?search=Multi%Like")
        blog_id = blogs_resp.json()["data"][0]["id"]

        # Multiple like/unlike cycles
        for _ in range(3):
            await client.post(f"/api/blogs/{blog_id}/like", headers=liker_headers)  # Like
            await client.post(f"/api/blogs/{blog_id}/like", headers=liker_headers)  # Unlike

        # Final like
        await client.post(f"/api/blogs/{blog_id}/like", headers=liker_headers)

        # Should only have one notification (or latest one)
        notif_resp = await client.get("/api/notifications", headers=author_headers)
        data = notif_resp.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_author_cannot_like_own_blog_notification(self, client: AsyncClient):
        """Test that authors don't get notifications for liking their own blogs"""
        author_headers = await _create_user(client, "SelfLikeAuthor")

        # Create blog
        create_resp = await client.post(
            "/api/blogs",
            data={"title": "Self Like Test", "content": "Author likes own blog"},
            headers=author_headers,
        )
        assert create_resp.status_code == 201

        blogs_resp = await client.get("/api/blogs?search=Self%Like")
        blog_id = blogs_resp.json()["data"][0]["id"]

        # Author tries to like own blog
        like_resp = await client.post(f"/api/blogs/{blog_id}/like", headers=author_headers)

        # Check notifications - author shouldn't get notification for own like
        notif_resp = await client.get("/api/notifications", headers=author_headers)
        data = notif_resp.json()
        assert data["total"] == 0