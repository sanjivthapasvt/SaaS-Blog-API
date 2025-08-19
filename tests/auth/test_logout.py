import pytest
from httpx import AsyncClient

from tests.auth_utils import _create_user


class TestLogout:
    """Test for logout functionality"""

    @pytest.mark.asyncio
    async def test_successful_logout(self, client: AsyncClient):
        """Test successful logout with valid token"""
        headers = await _create_user(client=client, username="logoutuser001")

        resp = await client.post("/auth/logout", headers=headers)
        assert resp.status_code == 200

        data = resp.json()
        assert (
            "logged out" in data["detail"].lower()
            or "success" in data["detail"].lower()
        )

    @pytest.mark.asyncio
    async def test_logout_without_token(self, client: AsyncClient):
        """Test logout fails without authentication token"""
        resp = await client.post("/auth/logout")
        assert resp.status_code == 401 or resp.status_code == 403
        assert "not authenticated" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token(self, client: AsyncClient):
        """Test logout fails with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}

        resp = await client.post("/auth/logout", headers=headers)
        assert resp.status_code == 401 or resp.status_code == 403

    @pytest.mark.asyncio
    async def test_double_logout(self, client: AsyncClient):
        """Test that logout twice with same token fails the second time"""
        headers = await _create_user(client=client, username="doublelogout")

        # First logout should succeed
        resp1 = await client.post("/auth/logout", headers=headers)
        assert resp1.status_code == 200

        # Second logout with same token should fail
        resp2 = await client.post("/auth/logout", headers=headers)
        assert resp2.status_code == 401 or resp2.status_code == 403
