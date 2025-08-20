import pytest
from httpx import AsyncClient


class TestUserRegistration:
    """Test for user registration functionality"""

    @pytest.mark.asyncio
    async def test_successful_registration(self, client: AsyncClient):
        """Test successful user registration"""
        register_payload = {
            "username": "newuser00001",
            "first_name": "New",
            "last_name": "User",
            "email": "newuser001@example.com",
            "password": "SecurePass123!",
        }

        resp = await client.post("/api/auth/register", json=register_payload)
        assert resp.status_code == 200, resp.text

        data = resp.json()
        assert set(data.keys()) == {"access_token", "refresh_token", "token_type"}
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    @pytest.mark.asyncio
    async def test_duplicate_username(self, client: AsyncClient):
        """Test registration fails with duplicate username"""
        payload = {
            "username": "duplicateuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "unique1@example.com",
            "password": "SecurePass123!",
        }

        # First registration
        resp1 = await client.post("/api/auth/register", json=payload)
        assert resp1.status_code == 200

        # Second registration with same username should fail
        payload["email"] = "unique2@example.com"
        resp2 = await client.post("/api/auth/register", json=payload)
        assert resp2.status_code == 400
        assert "username" in resp2.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_duplicate_email(self, client: AsyncClient):
        """Test registration fails with duplicate email"""
        email = "duplicate@example.com"

        payload1 = {
            "username": "user1",
            "first_name": "User",
            "last_name": "One",
            "email": email,
            "password": "SecurePass123!",
        }

        payload2 = {
            "username": "user2",
            "first_name": "User",
            "last_name": "Two",
            "email": email,  # Same email
            "password": "SecurePass123!",
        }

        resp1 = await client.post("/api/auth/register", json=payload1)
        assert resp1.status_code == 200

        resp2 = await client.post("/api/auth/register", json=payload2)
        assert resp2.status_code == 400
        assert (
            "email" in resp2.json()["detail"].lower()
            or "exists" in resp2.json()["detail"].lower()
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "invalid_email",
        [
            "notanemail",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            "",
        ],
    )
    async def test_invalid_email_formats(self, client: AsyncClient, invalid_email):
        """Test registration fails with invalid email formats"""
        payload = {
            "username": f"user_{invalid_email.replace('@', '_').replace('.', '_')}",
            "first_name": "Test",
            "last_name": "User",
            "email": invalid_email,
            "password": "SecurePass123!",
        }

        resp = await client.post("/api/auth/register", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "weak_password",
        [
            "123",  # Too short
            "password",  # No numbers/special chars
            "12345678",  # Only numbers
            "PASSWORD123",  # No lowercase
            "password123",  # No uppercase
            "",  # Empty
        ],
    )
    async def test_weak_passwords(self, client: AsyncClient, weak_password):
        """Test registration fails with weak passwords"""
        payload = {
            "username": f"user_{hash(weak_password) % 10000}",
            "first_name": "Test",
            "last_name": "User",
            "email": f"test_{hash(weak_password) % 10000}@example.com",
            "password": weak_password,
        }

        resp = await client.post("/api/auth/register", json=payload)
        assert resp.status_code == 422 or resp.status_code == 400

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "field", ["username", "first_name", "last_name", "email", "password"]
    )
    async def test_missing_required_fields(self, client: AsyncClient, field):
        """Test registration fails with missing required fields"""
        payload = {
            "username": "testuser",
            "first_name": "Test",
            "last_name": "User",
            "email": "test@example.com",
            "password": "SecurePass123!",
        }

        del payload[field]  # Remove the field

        resp = await client.post("/api/auth/register", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_username_length_limits(self, client: AsyncClient):
        """Test username length validation"""
        # Too long username
        long_username = "a" * 51  # 50 char limit
        payload = {
            "username": long_username,
            "first_name": "Test",
            "last_name": "User",
            "email": "longuser@example.com",
            "password": "SecurePass123!",
        }

        resp = await client.post("/api/auth/register", json=payload)
        assert resp.status_code == 422 or resp.status_code == 400


class TestUserLogin:
    """Test for user login functionality"""

    @pytest.fixture
    def registered_user_data(self):
        """Return user data for registration"""
        return {
            "username": "loginuser",
            "first_name": "Login",
            "last_name": "User",
            "email": "loginuser@example.com",
            "password": "SecurePass123!",
        }

    @pytest.fixture
    async def registered_user(self, client: AsyncClient, registered_user_data):
        """Create a registered user for login tests"""
        resp = await client.post("/api/auth/register", json=registered_user_data)
        assert resp.status_code == 200
        return registered_user_data

    @pytest.mark.asyncio
    async def test_successful_login(self, client: AsyncClient, registered_user_data):
        """Test successful login with valid credentials"""
        # First register the user
        resp = await client.post("/api/auth/register", json=registered_user_data)
        assert resp.status_code == 200

        login_payload = {
            "username": registered_user_data["username"],
            "password": registered_user_data["password"],
        }

        resp = await client.post("/api/auth/login", json=login_payload)
        assert resp.status_code == 200, resp.text

        data = resp.json()
        assert set(data.keys()) == {"access_token", "refresh_token", "token_type"}
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_with_email(self, client: AsyncClient, registered_user_data):
        """Test login using email instead of username"""
        # First register the user
        login_payload = {
            "username": registered_user_data["email"],  # Using email as username
            "password": registered_user_data["password"],
        }

        resp = await client.post("/api/auth/login", json=login_payload)
        # This should fail cause I haven't implemented yet
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_wrong_password(self, client: AsyncClient, registered_user_data):
        """Test login fails with incorrect password"""
        login_payload = {
            "username": registered_user_data["username"],
            "password": "wrongpassword",
        }

        resp = await client.post("/api/auth/login", json=login_payload)
        assert resp.status_code == 400
        assert "incorrect" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_nonexistent_user(self, client: AsyncClient):
        """Test login fails with non-existent username"""
        login_payload = {"username": "nonexistentuser", "password": "anypassword"}

        resp = await client.post("/api/auth/login", json=login_payload)
        assert resp.status_code == 400 or resp.status_code == 401

    @pytest.mark.asyncio
    @pytest.mark.parametrize("field", ["username", "password"])
    async def test_missing_login_fields(self, client: AsyncClient, field):
        """Test login fails with missing credentials"""
        payload = {"username": "testuser", "password": "password"}
        del payload[field]

        resp = await client.post("/api/auth/login", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_empty_credentials(self, client: AsyncClient):
        """Test login fails with empty credentials"""
        login_payload = {"username": "", "password": ""}

        resp = await client.post("/api/auth/login", json=login_payload)
        assert resp.status_code == 422 or resp.status_code == 400
