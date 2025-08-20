import pytest
from datetime import datetime
from uuid import uuid4
from httpx import AsyncClient

from app.blogs.schema import BlogResponse
from tests.schema.global_schema import PaginatedResponse
from tests.schema.user_schema import CurrentUserRead, UserRead
from tests.blogs.test_blogs_crud import validate_response


class TestUserEndpoints:
    """Test for all user endpoints"""

    async def _create_test_user(self, client: AsyncClient, suffix: str = None) -> tuple[dict[str, str], dict]: # type: ignore
        """helper to create a test user and return headers + user data"""
        unique = uuid4().hex[:8] if not suffix else suffix
        user_data = {
            "username": f"testuser_{unique}",
            "first_name": "Test",
            "last_name": "User",
            "email": f"testuser_{unique}@example.com",
            "password": "Secret123@",
        }
        
        resp = await client.post("/auth/register", json=user_data)
        assert resp.status_code == 200
        
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        return headers, user_data

    # =============================================================================
    # GET /api/users/me - Current User Info
    # =============================================================================
    
    @pytest.mark.asyncio
    async def test_get_current_user_info_success(self, client: AsyncClient):
        """test successful retrieval of current user info"""
        headers, user_data = await self._create_test_user(client)
        
        resp = await client.get("/api/users/me", headers=headers)
        assert resp.status_code == 200
        
        validated_user = validate_response(resp.json(), CurrentUserRead)
        assert isinstance(validated_user.id, int)
        assert validated_user.username == user_data["username"]
        assert validated_user.full_name == f"{user_data['first_name']} {user_data['last_name']}"
        assert validated_user.email == user_data["email"]
        assert isinstance(validated_user.joined_at, datetime)
        assert validated_user.profile_pic is None 

    @pytest.mark.asyncio
    async def test_get_current_user_info_unauthorized(self, client: AsyncClient):
        """Test getting current user info without authentication"""
        resp = await client.get("/api/users/me")
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_current_user_info_invalid_token(self, client: AsyncClient):
        """Test getting current user info with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        resp = await client.get("/api/users/me", headers=headers)
        assert resp.status_code == 401

    # =============================================================================
    # PATCH /api/users/me - Update User Profile
    # =============================================================================

    @pytest.mark.asyncio
    async def test_update_user_profile_full_name_only(self, client: AsyncClient):
        """Test updating only the full name"""
        headers, _ = await self._create_test_user(client)
        
        resp = await client.patch(
            "/api/users/me", 
            data={"full_name": "Updated Name"}, 
            headers=headers
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
        headers, _ = await self._create_test_user(client)
        
        # Create a dummy image file for testing
        image_content = b"fake_image_content"
        files = {"profile_pic": ("profile.png", image_content, "image/png")}
        data = {"full_name": "Updated With Image"}
        
        resp = await client.patch(
            "/api/users/me", 
            data=data, 
            files=files, 
            headers=headers
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
        headers, _ = await self._create_test_user(client)
        
        image_content = b"fake_image_content"
        files = {"profile_pic": ("profile.jpg", image_content, "image/jpeg")}
        
        resp = await client.patch(
            "/api/users/me", 
            files=files, 
            headers=headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_user_profile_unauthorized(self, client: AsyncClient):
        """Test updating profile without authentication"""
        resp = await client.patch(
            "/api/users/me", 
            data={"full_name": "Should Fail"}
        )
        assert resp.status_code == 403

    # =============================================================================
    # POST /api/users/me/password - Change Password
    # =============================================================================

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient):
        """Test successful password change"""
        headers, user_data = await self._create_test_user(client)
        
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
            "/auth/login", 
            json={
                "username": user_data["username"], 
                "password": "Secret123@"
            }
        )
        assert login_resp.status_code == 400
        
        # Verify new password works
        login_resp = await client.post(
            "/auth/login", 
            json={
                "username": user_data["username"], 
                "password": "NewSecret123@"
            }
        )
        assert login_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_password(self, client: AsyncClient):
        """Test password change with wrong current password"""
        headers, _ = await self._create_test_user(client)
        
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
        headers, _ = await self._create_test_user(client)
        
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
        assert resp.status_code == 403

    # =============================================================================
    # GET /api/users/me/blogs - Current User's Blogs
    # =============================================================================

    @pytest.mark.asyncio
    async def test_get_current_user_blogs_empty(self, client: AsyncClient):
        """Test getting current user's blogs when they have none"""
        headers, _ = await self._create_test_user(client)
        
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
        headers, _ = await self._create_test_user(client)
        
        resp = await client.get(
            "/api/users/me/blogs?limit=5&offset=0&search=test", 
            headers=headers
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
        assert resp.status_code == 403

    # =============================================================================
    # GET /api/users - List All Users
    # =============================================================================

    @pytest.mark.asyncio
    async def test_list_users_success(self, client: AsyncClient):
        """Test successful listing of users"""
        headers, _ = await self._create_test_user(client)
        
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
        headers, user_data = await self._create_test_user(client)
        
        resp = await client.get(
            f"/api/users?search={user_data['first_name']}", 
            headers=headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_users_with_pagination(self, client: AsyncClient):
        """Test listing users with pagination"""
        headers, _ = await self._create_test_user(client)
        
        resp = await client.get(
            "/api/users?limit=5&offset=0", 
            headers=headers
        )
        assert resp.status_code == 200
        
        data = resp.json()
        assert data["limit"] == 5
        assert data["offset"] == 0

    @pytest.mark.asyncio
    async def test_list_users_unauthorized(self, client: AsyncClient):
        """Test listing users without authentication"""
        resp = await client.get("/api/users")
        assert resp.status_code == 403

    # =============================================================================
    # GET /api/users/{user_id}/followers - List User Followers
    # =============================================================================

    @pytest.mark.asyncio
    async def test_list_user_followers_success(self, client: AsyncClient):
        """Test listing user followers"""
        headers, _ = await self._create_test_user(client)
        
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
        headers, _ = await self._create_test_user(client)
        
        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]
        
        resp = await client.get(
            f"/api/users/{user_id}/followers?limit=10&offset=0", 
            headers=headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_user_followers_nonexistent_user(self, client: AsyncClient):
        """Test listing followers for non-existent user"""
        headers, _ = await self._create_test_user(client)
        
        resp = await client.get("/api/users/99999/followers", headers=headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_user_followers_unauthorized(self, client: AsyncClient):
        """Test listing user followers without authentication"""
        resp = await client.get("/api/users/1/followers")
        assert resp.status_code == 403

    # =============================================================================
    # GET /api/users/{user_id}/following - List User Following
    # =============================================================================

    @pytest.mark.asyncio
    async def test_list_user_following_success(self, client: AsyncClient):
        """Test listing users that a user is following"""
        headers, _ = await self._create_test_user(client)
        
        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]
        
        resp = await client.get(f"/api/users/{user_id}/following", headers=headers)
        assert resp.status_code == 200
        
        validated_response = validate_response(resp.json(), PaginatedResponse[UserRead])
        assert isinstance(validated_response.total, int)

    @pytest.mark.asyncio
    async def test_list_user_following_with_search(self, client: AsyncClient):
        """Test listing following users with search"""
        headers, _ = await self._create_test_user(client)
        
        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]
        
        resp = await client.get(
            f"/api/users/{user_id}/following?search=test", 
            headers=headers
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_user_following_unauthorized(self, client: AsyncClient):
        """Test listing user following without authentication"""
        resp = await client.get("/api/users/1/following")
        assert resp.status_code == 403

    # =============================================================================
    # POST /api/users/{user_id}/follow - Follow User
    # =============================================================================

    @pytest.mark.asyncio
    async def test_follow_user_success(self, client: AsyncClient):
        """Test successfully following another user"""
        # Create two users
        headers1, _ = await self._create_test_user(client, "follower")
        headers2, _ = await self._create_test_user(client, "followee")
        
        # Get the second user's ID
        user2_resp = await client.get("/api/users/me", headers=headers2)
        user2_id = user2_resp.json()["id"]
        
        # Follow the second user with first user's credentials
        resp = await client.post(f"/api/users/{user2_id}/follow", headers=headers1)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_follow_user_self(self, client: AsyncClient):
        """Test following yourself (should fail)"""
        headers, _ = await self._create_test_user(client)
        
        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]
        
        resp = await client.post(f"/api/users/{user_id}/follow", headers=headers)
        assert resp.status_code == 400 

    @pytest.mark.asyncio
    async def test_follow_nonexistent_user(self, client: AsyncClient):
        """Test following a non-existent user"""
        headers, _ = await self._create_test_user(client)
        
        resp = await client.post("/api/users/99999/follow", headers=headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_follow_user_unauthorized(self, client: AsyncClient):
        """Test following user without authentication"""
        resp = await client.post("/api/users/1/follow")
        assert resp.status_code == 403

    # =============================================================================
    # DELETE /api/users/{user_id}/follow - Unfollow User
    # =============================================================================

    @pytest.mark.asyncio
    async def test_unfollow_user_success(self, client: AsyncClient):
        """Test successfully unfollowing a user"""
        # Create two users
        headers1, _ = await self._create_test_user(client, "unfollower")
        headers2, _ = await self._create_test_user(client, "unfollowee")
        
        user2_resp = await client.get("/api/users/me", headers=headers2)
        user2_id = user2_resp.json()["id"]
        
        # First follow the user
        follow_resp = await client.post(f"/api/users/{user2_id}/follow", headers=headers1)
        assert follow_resp.status_code == 200
        
        # Then unfollow
        unfollow_resp = await client.delete(f"/api/users/{user2_id}/follow", headers=headers1)
        assert unfollow_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_unfollow_user_not_following(self, client: AsyncClient):
        """Test unfollowing a user you're not following"""
        headers1, _ = await self._create_test_user(client, "notfollower")
        headers2, _ = await self._create_test_user(client, "notfollowee")
        
        user2_resp = await client.get("/api/users/me", headers=headers2)
        user2_id = user2_resp.json()["id"]
        
        resp = await client.delete(f"/api/users/{user2_id}/follow", headers=headers1)
        assert resp.status_code == 400 

    @pytest.mark.asyncio
    async def test_unfollow_nonexistent_user(self, client: AsyncClient):
        """Test unfollowing a non-existent user"""
        headers, _ = await self._create_test_user(client)
        
        resp = await client.delete("/api/users/99999/follow", headers=headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_unfollow_user_unauthorized(self, client: AsyncClient):
        """Test unfollowing user without authentication"""
        resp = await client.delete("/api/users/1/follow")
        assert resp.status_code == 403

    # =============================================================================
    # GET /api/users/{user_id}/blogs - List User's Blogs
    # =============================================================================

    @pytest.mark.asyncio
    async def test_list_user_blogs_success(self, client: AsyncClient):
        """Test listing a specific user's blogs"""
        headers, _ = await self._create_test_user(client)
        
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
        headers, _ = await self._create_test_user(client)
        
        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]
        
        resp = await client.get(f"/api/users/{user_id}/blogs?limit=5&offset=0")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_user_blogs_with_search(self, client: AsyncClient):
        """Test listing user blogs with search"""
        headers, _ = await self._create_test_user(client)
        
        user_resp = await client.get("/api/users/me", headers=headers)
        user_id = user_resp.json()["id"]
        
        resp = await client.get(f"/api/users/{user_id}/blogs?search=test")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_list_user_blogs_nonexistent_user(self, client: AsyncClient):
        """Test listing blogs for non-existent user"""
        resp = await client.get("/api/users/99999/blogs")
        assert resp.status_code == 404

