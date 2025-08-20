import pytest
from httpx import AsyncClient

from app.blogs.schema import BlogResponse
from tests.blogs.test_blogs_crud import validate_response
from tests.schema.global_schema import PaginatedResponse
from tests.schema.user_schema import UserRead
from tests.utils.auth_utils import _create_test_user


class TestListUserEndpoints:
    """Test for list user endpoints"""

    @pytest.mark.asyncio
    async def test_list_users_success(self, client: AsyncClient):
        """Test successful listing of users"""
        headers, _ = await _create_test_user(client)

        resp = await client.get("/api/users", headers=headers)
        assert resp.status_code == 200

        validated_response = validate_response(resp.json(), PaginatedResponse[UserRead])
        assert validated_response.total >= 1
        assert isinstance(validated_response.limit, int)
        assert isinstance(validated_response.offset, int)
        assert len(validated_response.data) >= 1

        # Validate user structure
        for user in validated_response.data:
            assert isinstance(user.id, int)
            assert isinstance(user.full_name, str)
            assert user.profile_pic is None or isinstance(user.profile_pic, str)

    @pytest.mark.asyncio
    async def test_list_users_with_search(self, client: AsyncClient):
        """Test listing users with search parameter"""
        headers, user_data = await _create_test_user(client)

        resp = await client.get(
            f"/api/users?search={user_data['first_name']}", headers=headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, client: AsyncClient):
        """Test listing users with pagination"""
        headers, _ = await _create_test_user(client)

        resp = await client.get("/api/users?limit=5&offset=0", headers=headers)
        assert resp.status_code == 200

        data = resp.json()
        assert data["limit"] == 5
        assert data["offset"] == 0

    @pytest.mark.asyncio
    async def test_list_users_unauthorized(self, client: AsyncClient):
        """Test listing users without authentication"""
        resp = await client.get("/api/users")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_user_followers_success(self, client: AsyncClient):
        """Test listing user followers"""
        headers, _ = await _create_test_user(client)

        # Get current user info to get user ID
        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]

        resp = await client.get(f"/api/users/{user_id}/followers", headers=headers)
        assert resp.status_code == 200

        validated_response = validate_response(resp.json(), PaginatedResponse[UserRead])
        assert isinstance(validated_response.total, int)
        assert isinstance(validated_response.limit, int)
        assert isinstance(validated_response.offset, int)

    @pytest.mark.asyncio
    async def test_list_user_followers_with_pagination(self, client: AsyncClient):
        """Test listing user followers with pagination"""
        headers, _ = await _create_test_user(client)

        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]

        resp = await client.get(
            f"/api/users/{user_id}/followers?limit=10&offset=0", headers=headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_user_followers_nonexistent_user(self, client: AsyncClient):
        """Test listing followers for non-existent user"""
        headers, _ = await _create_test_user(client)

        resp = await client.get("/api/users/99999/followers", headers=headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_user_followers_unauthorized(self, client: AsyncClient):
        """Test listing user followers without authentication"""
        resp = await client.get("/api/users/1/followers")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_user_following_success(self, client: AsyncClient):
        """Test listing users that a user is following"""
        headers, _ = await _create_test_user(client)

        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]

        resp = await client.get(f"/api/users/{user_id}/following", headers=headers)
        assert resp.status_code == 200

        validated_response = validate_response(resp.json(), PaginatedResponse[UserRead])
        assert isinstance(validated_response.total, int)

    @pytest.mark.asyncio
    async def test_list_user_following_with_search(self, client: AsyncClient):
        """Test listing following users with search"""
        headers, _ = await _create_test_user(client)

        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]

        resp = await client.get(
            f"/api/users/{user_id}/following?search=test", headers=headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_user_following_unauthorized(self, client: AsyncClient):
        """Test listing user following without authentication"""
        resp = await client.get("/api/users/1/following")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_list_user_blogs_success(self, client: AsyncClient):
        """Test listing a specific user's blogs"""
        headers, _ = await _create_test_user(client)

        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]

        resp = await client.get(f"/api/users/{user_id}/blogs")
        assert resp.status_code == 200

        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])

        assert validated_data.total == 0
        assert validated_data.limit == 10
        assert validated_data.offset == 0
        assert len(validated_data.data) == 0

    @pytest.mark.asyncio
    async def test_list_user_blogs_with_pagination(self, client: AsyncClient):
        """Test listing user blogs with pagination"""
        headers, _ = await _create_test_user(client)

        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]

        resp = await client.get(f"/api/users/{user_id}/blogs?limit=5&offset=0")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_user_blogs_with_search(self, client: AsyncClient):
        """Test listing user blogs with search"""
        headers, _ = await _create_test_user(client)

        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]

        resp = await client.get(f"/api/users/{user_id}/blogs?search=test")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_user_blogs_nonexistent_user(self, client: AsyncClient):
        """Test listing blogs for non-existent user"""
        resp = await client.get("/api/users/99999/blogs")
        assert resp.status_code == 404
