from datetime import datetime

import pytest
from httpx import AsyncClient

from app.users.schema import CurrentUserRead
from tests.schema.blog_and_comment_schema import BlogResponse
from tests.schema.global_schema import PaginatedResponse
from tests.utils.auth_utils import _create_test_user
from tests.utils.validator import validate_response


class TestUserMeEndpoints:
    """
    Test for user me endpoints
    """

    @pytest.mark.asyncio
    async def test_get_current_user_info_success(self, client: AsyncClient):
        """test successful retrieval of current user info"""
        headers, user_data = await _create_test_user(client)

        resp = await client.get("/api/users/me", headers=headers)
        assert resp.status_code == 200

        validated_user = validate_response(resp.json(), CurrentUserRead)
        assert isinstance(validated_user.id, int)
        assert validated_user.username == user_data["username"]
        assert (
            validated_user.full_name
            == f"{user_data['first_name']} {user_data['last_name']}"
        )
        assert validated_user.email == user_data["email"]
        assert isinstance(validated_user.joined_at, datetime)
        assert validated_user.profile_pic is None

    @pytest.mark.asyncio
    async def test_get_current_user_info_unauthorized(self, client: AsyncClient):
        """Test getting current user info without authentication"""
        resp = await client.get("/api/users/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_info_invalid_token(self, client: AsyncClient):
        """Test getting current user info with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        resp = await client.get("/api/users/me", headers=headers)
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_profile_full_name_only(self, client: AsyncClient):
        """Test updating only the full name"""
        headers, _ = await _create_test_user(client)

        resp = await client.patch(
            "/api/users/me", data={"full_name": "Updated Name"}, headers=headers
        )
        assert resp.status_code == 200

        # Verify the update
        resp = await client.get("/api/users/me", headers=headers)
        data = resp.json()
        assert data["full_name"] == "Updated Name"
        assert data["profile_pic"] is None

    @pytest.mark.asyncio
    async def test_update_user_profile_with_image(self, client: AsyncClient):
        """Test updating profile with image"""
        headers, _ = await _create_test_user(client)

        # Create a dummy image file for testing
        image_content = b"fake_image_content"
        files = {"profile_pic": ("profile.png", image_content, "image/png")}
        data = {"full_name": "Updated With Image"}

        resp = await client.patch(
            "/api/users/me", data=data, files=files, headers=headers
        )
        assert resp.status_code == 200

        # Verify update
        resp = await client.get("/api/users/me", headers=headers)
        user_data = resp.json()
        assert user_data["full_name"] == "Updated With Image"
        assert user_data["profile_pic"] is not None
        assert isinstance(user_data["profile_pic"], str)

    @pytest.mark.asyncio
    async def test_update_user_profile_image_only(self, client: AsyncClient):
        """Test updating only the profile image"""
        headers, _ = await _create_test_user(client)

        image_content = b"fake_image_content"
        files = {"profile_pic": ("profile.jpg", image_content, "image/jpeg")}

        resp = await client.patch("/api/users/me", files=files, headers=headers)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_user_profile_unauthorized(self, client: AsyncClient):
        """Test updating profile without authentication"""
        resp = await client.patch("/api/users/me", data={"full_name": "Should Fail"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient):
        """Test successful password change"""
        headers, user_data = await _create_test_user(client)

        resp = await client.post(
            "/api/users/me/password",
            json={
                "current_password": "Secret123@",
                "new_password": "NewSecret123@",
                "again_new_password": "NewSecret123@",
            },
            headers=headers,
        )
        assert resp.status_code == 200

        # Verify old password doesn't work
        login_resp = await client.post(
            "/api/auth/login",
            json={"username": user_data["username"], "password": "Secret123@"},
        )
        assert login_resp.status_code == 400

        # Verify new password works
        login_resp = await client.post(
            "/api/auth/login",
            json={"username": user_data["username"], "password": "NewSecret123@"},
        )
        assert login_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_password(self, client: AsyncClient):
        """Test password change with wrong current password"""
        headers, _ = await _create_test_user(client)

        resp = await client.post(
            "/api/users/me/password",
            json={
                "current_password": "WrongPassword",
                "new_password": "NewSecret123@",
                "again_new_password": "NewSecret123@",
            },
            headers=headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_change_password_mismatch_new_passwords(self, client: AsyncClient):
        """Test password change with mismatched new passwords"""
        headers, _ = await _create_test_user(client)

        resp = await client.post(
            "/api/users/me/password",
            json={
                "current_password": "Secret123@",
                "new_password": "NewSecret123@",
                "again_new_password": "DifferentSecret123@",
            },
            headers=headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_change_password_unauthorized(self, client: AsyncClient):
        """Test password change without authentication"""
        resp = await client.post(
            "/api/users/me/password",
            json={
                "current_password": "Secret123@",
                "new_password": "NewSecret123@",
                "again_new_password": "NewSecret123@",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_blogs_empty(self, client: AsyncClient):
        """Test getting current user's blogs when they have none"""
        headers, _ = await _create_test_user(client)

        resp = await client.get("/api/users/me/blogs", headers=headers)
        assert resp.status_code == 200

        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        assert validated_data.total == 0
        assert validated_data.limit == 10
        assert validated_data.offset == 0
        assert len(validated_data.data) == 0

    @pytest.mark.asyncio
    async def test_get_current_user_blogs_with_pagination(self, client: AsyncClient):
        """Test getting current user's blogs with pagination parameters"""
        headers, _ = await _create_test_user(client)

        resp = await client.get(
            "/api/users/me/blogs?limit=5&offset=0&search=test", headers=headers
        )
        assert resp.status_code == 200

        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        assert validated_data.total == 0
        assert validated_data.limit == 5
        assert validated_data.offset == 0
        assert len(validated_data.data) == 0

    @pytest.mark.asyncio
    async def test_get_current_user_blogs_unauthorized(self, client: AsyncClient):
        """Test getting current user's blogs without authentication"""
        resp = await client.get("/api/users/me/blogs")
        assert resp.status_code == 401
