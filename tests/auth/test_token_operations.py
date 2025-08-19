import jwt
import pytest
from httpx import AsyncClient



class TestTokenOperations:
    """Test suite for token-related operations"""

    @pytest.fixture
    def token_user_data(self):
        """Return user data for token tests"""
        return {
            "username": "tokenuser",
            "first_name": "Token",
            "last_name": "User",
            "email": "tokenuser@example.com",
            "password": "SecurePass123!",
        }

    @pytest.mark.asyncio
    async def test_access_token_structure(self, client: AsyncClient, token_user_data):
        """Test that access token has proper JWT structure"""
        # Register and get tokens

        resp = await client.post("/auth/register", json=token_user_data)
        assert resp.status_code == 200
        tokens = resp.json()
        
        access_token = tokens["access_token"]
        
        # Decode without verification to check structure
        try:
            decoded = jwt.decode(access_token, options={"verify_signature": False})
            assert "sub" in decoded #sub
            assert "exp" in decoded  # Expiration
        except jwt.InvalidTokenError:
            pytest.fail("Access token is not a valid JWT")

    @pytest.mark.asyncio
    async def test_refresh_token_functionality(self, client: AsyncClient):
        """Test refresh token generates new valid tokens"""
        # Login and get tokens
        login_payload = {
            "username": "tokenuser",
            "password": "SecurePass123!"
        }
        resp = await client.post("/auth/login", json=login_payload)
        assert resp.status_code == 200
        initial_tokens = resp.json()
        
        refresh_token = initial_tokens["refresh_token"]
        
        resp = await client.post(f"/auth/refresh?refresh_token={refresh_token}")
        assert resp.status_code == 200
        
        data = resp.json()
        assert set(data.keys()) == {"access_token", "refresh_token", "token_type"}
        assert data["token_type"] == "bearer"
        
        # New tokens should be different from original
        assert data["access_token"] != initial_tokens["access_token"]
        assert data["refresh_token"] != initial_tokens["refresh_token"]

    @pytest.mark.asyncio
    async def test_malformed_refresh_token(self, client: AsyncClient):
        """Test that malformed refresh tokens are rejected"""
        malformed_tokens = [
            "not.a.token",
            "invalid_token_format",
            "",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",  # Invalid JWT
        ]
        
        for token in malformed_tokens:
            resp = await client.post(f"/auth/refresh?refresh_token={token}")
            assert resp.status_code == 401
