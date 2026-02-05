import pytest
from httpx import AsyncClient

from tests.utils.auth_utils import _create_test_user


class TestUserFollowEndpoints:
    """
    Tests for user follow and unfollow endpoints
    """

    @pytest.mark.asyncio
    async def test_follow_user_success(self, client: AsyncClient):
        """Test successfully following another user"""
        # Create two users
        headers1, _ = await _create_test_user(client, "follower")
        headers2, _ = await _create_test_user(client, "followee")

        # Get the second user's ID
        user2_resp = await client.get("/api/users/me", headers=headers2)
        user2_id = user2_resp.json()["id"]

        # Follow the second user with first user's credentials
        resp = await client.post(f"/api/users/{user2_id}/follow", headers=headers1)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_follow_user_self(self, client: AsyncClient):
        """Test following yourself (should fail)"""
        headers, _ = await _create_test_user(client)

        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]

        resp = await client.post(f"/api/users/{user_id}/follow", headers=headers)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_follow_nonexistent_user(self, client: AsyncClient):
        """Test following a non-existent user"""
        headers, _ = await _create_test_user(client)

        resp = await client.post("/api/users/99999/follow", headers=headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_follow_user_unauthorized(self, client: AsyncClient):
        """Test following user without authentication"""
        resp = await client.post("/api/users/1/follow")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_unfollow_user_success(self, client: AsyncClient):
        """Test successfully unfollowing a user"""
        # Create two users
        headers1, _ = await _create_test_user(client, "unfollower")
        headers2, _ = await _create_test_user(client, "unfollowee")

        user2_resp = await client.get("/api/users/me", headers=headers2)
        user2_id = user2_resp.json()["id"]

        # First follow the user
        follow_resp = await client.post(
            f"/api/users/{user2_id}/follow", headers=headers1
        )
        assert follow_resp.status_code == 200

        # Then unfollow
        unfollow_resp = await client.delete(
            f"/api/users/{user2_id}/follow", headers=headers1
        )
        assert unfollow_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_unfollow_user_not_following(self, client: AsyncClient):
        """Test unfollowing a user you're not following"""
        headers1, _ = await _create_test_user(client, "notfollower")
        headers2, _ = await _create_test_user(client, "notfollowee")

        user2_resp = await client.get("/api/users/me", headers=headers2)
        user2_id = user2_resp.json()["id"]

        resp = await client.delete(f"/api/users/{user2_id}/follow", headers=headers1)
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_unfollow_nonexistent_user(self, client: AsyncClient):
        """Test unfollowing a non-existent user"""
        headers, _ = await _create_test_user(client)

        resp = await client.delete("/api/users/99999/follow", headers=headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unfollow_user_unauthorized(self, client: AsyncClient):
        """Test unfollowing user without authentication"""
        resp = await client.delete("/api/users/1/follow")
        assert resp.status_code == 401
