from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestUserEndpointsIntegration:
    """Integration tests for user endpoints"""

    @pytest.mark.asyncio
    async def test_complete_user_workflow(self, client: AsyncClient):
        """Test a complete user workflow: register, update profile, follow/unfollow"""
        # Create two users
        user1_data = {
            "username": f"user1_{uuid4().hex[:8]}",
            "first_name": "User",
            "last_name": "One",
            "email": f"user1_{uuid4().hex[:8]}@example.com",
            "password": "Secret123@",
        }

        user2_data = {
            "username": f"user2_{uuid4().hex[:8]}",
            "first_name": "User",
            "last_name": "Two",
            "email": f"user2_{uuid4().hex[:8]}@example.com",
            "password": "Secret123@",
        }

        # Register users
        resp1 = await client.post("/api/auth/register", json=user1_data)
        resp2 = await client.post("/api/auth/register", json=user2_data)

        headers1 = {"Authorization": f"Bearer {resp1.json()['access_token']}"}
        headers2 = {"Authorization": f"Bearer {resp2.json()['access_token']}"}

        # Get user IDs
        user1_resp = await client.get("/api/users/me", headers=headers1)
        user2_resp = await client.get("/api/users/me", headers=headers2)

        user1_id = user1_resp.json()["id"]
        user2_id = user2_resp.json()["id"]

        # User 1 follows User 2
        follow_resp = await client.post(
            f"/api/users/{user2_id}/follow", headers=headers1
        )
        assert follow_resp.status_code == 200

        # Check User 2's followers
        followers_resp = await client.get(
            f"/api/users/{user2_id}/followers", headers=headers1
        )
        assert followers_resp.status_code == 200
        followers_data = followers_resp.json()
        assert followers_data["total"] >= 1

        # Check User 1's following
        following_resp = await client.get(
            f"/api/users/{user1_id}/following", headers=headers1
        )
        assert following_resp.status_code == 200
        following_data = following_resp.json()
        assert following_data["total"] >= 1

        # User 1 unfollows User 2
        unfollow_resp = await client.delete(
            f"/api/users/{user2_id}/follow", headers=headers1
        )
        assert unfollow_resp.status_code == 200

        # Update User 1's profile
        update_resp = await client.patch(
            "/api/users/me", data={"full_name": "Updated User One"}, headers=headers1
        )
        assert update_resp.status_code == 200

        # Verify the update
        updated_user_resp = await client.get("/api/users/me", headers=headers1)
        assert updated_user_resp.json()["full_name"] == "Updated User One"

    @pytest.mark.asyncio
    async def test_user_search_functionality(self, client: AsyncClient):
        """Test search functionality across user endpoints"""
        headers, _ = await self._create_test_user_with_name(
            client, "Searchable", f"User{uuid4().hex[:8]}"
        )

        # Search for the user in the users list
        search_resp = await client.get(f"/api/users?search=Searchable", headers=headers)
        assert search_resp.status_code == 200
        search_data = search_resp.json()

        # Should find at least our created user
        found = any("Searchable" in user["full_name"] for user in search_data["data"])
        assert found

    async def _create_test_user_with_name(
        self, client: AsyncClient, first_name: str, last_name: str
    ) -> tuple[dict[str, str], dict]:
        """Helper to create a test user with specific full name"""
        unique = uuid4().hex[:8]
        user_data = {
            "username": f"testuser_{unique}",
            "first_name": first_name,
            "last_name": last_name,
            "email": f"testuser_{unique}@example.com",
            "password": "Secret123@",
        }

        resp = await client.post("/api/auth/register", json=user_data)
        assert resp.status_code == 200

        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        return headers, user_data
