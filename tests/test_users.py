from datetime import datetime
from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.auth_utils import _create_user
from tests.schema.global_schema import PaginatedResponse
from tests.schema.user_schema import CurrentUserRead, UserRead
from tests.blogs.test_blog_crud import validate_response


class TestUserEndpointValidation:
    """Test user-related endpoints with validation"""

    @pytest.mark.asyncio
    async def test_current_user_info_validation(self, client: AsyncClient):
        """Test current user info endpoint with validation"""
        headers = await _create_user(client, "CurrentUserValidation")
        
        resp = await client.get("/api/users/me", headers=headers)
        assert resp.status_code == 200
        
        validated_user = validate_response(resp.json(), CurrentUserRead)
        assert isinstance(validated_user.id, int)
        assert validated_user.username is not None  # Should have username after creation
        assert validated_user.full_name is not None
        assert isinstance(validated_user.joined_at, datetime)
        # profile_pic and email can be None
        assert validated_user.profile_pic is None or isinstance(validated_user.profile_pic, str)
        assert validated_user.email is None or isinstance(validated_user.email, str)

    @pytest.mark.asyncio
    async def test_list_users_validation(self, client: AsyncClient):
        """Test listing users with response validation"""
        headers = await _create_user(client, "ListUsersValidation")
        
        resp = await client.get("/api/users", headers=headers)
        assert resp.status_code == 200
        
        validated_response = validate_response(resp.json(), PaginatedResponse[UserRead])
        assert validated_response.total >= 1  # At least the user we created
        assert isinstance(validated_response.limit, int)
        assert isinstance(validated_response.offset, int)
        assert len(validated_response.data) >= 1
        
        # Validate user structure
        for user in validated_response.data:
            assert isinstance(user.id, int)
            assert isinstance(user.full_name, str)
            assert user.profile_pic is None or isinstance(user.profile_pic, str)



async def _auth_header(client: AsyncClient) -> dict[str, str]:
    unique = uuid4().hex[:8]
    reg = await client.post(
        "/auth/register",
        json={
            "username": f"blogger_{unique}",
            "first_name": "Blog",
            "last_name": "Ger",
            "email": f"blogger_{unique}@example.com",
            "password": "Secret123@",
        },
    )
    assert reg.status_code == 200, reg.text
    token = reg.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_user_me(client: AsyncClient):
    headers = await _auth_header(client)
    resp1 = await client.get("/api/users/me", headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert set(data1.keys()) == {
        "id",
        "username",
        "full_name",
        "profile_pic",
        "email",
        "joined_at",
    }


@pytest.mark.asyncio
async def test_user_update_profile(client: AsyncClient):
    headers = await _auth_header(client)

    # update only full name

    resp1 = await client.patch(
        "/api/users/me", data={"full_name": "updated_name"}, headers=headers
    )
    assert resp1.status_code == 200

    resp2 = await client.get("/api/users/me", headers=headers)
    assert resp2.status_code == 200
    data1 = resp2.json()
    assert data1["full_name"] == "updated_name"
    assert data1["profile_pic"] == None

    # update user profile with full_name and profile_pic #1
    with open("tests/test1.png", "rb") as f:
        data = {
            "full_name": "updated_name_again",
        }
        files = {"profile_pic": ("first.png", f, "image/png")}
        resp3 = await client.patch(
            "/api/users/me", data=data, files=files, headers=headers
        )

    assert resp3.status_code == 200

    resp4 = await client.get("/api/users/me", headers=headers)
    data3 = resp4.json()
    assert data3["full_name"] == "updated_name_again"
    assert isinstance(data3["profile_pic"], str)

    # update user profile with full_name and profile_pic #2
    with open("tests/test2.jpeg", "rb") as f:
        files = {"profile_pic": ("second.png", f, "image/png")}
        resp5 = await client.patch("/api/users/me", files=files, headers=headers)
    assert resp5.status_code == 200

    resp6 = await client.get("/api/users/me", headers=headers)
    data4 = resp6.json()
    assert data4["full_name"] == "updated_name_again"
    assert isinstance(data4["profile_pic"], str)


@pytest.mark.asyncio
async def test_user_change_password(client: AsyncClient):
    headers = await _auth_header(client)
    resp = await client.post(
        "/api/users/me/password",
        json={
            "current_password": "Secret123@",
            "new_password": "Secret123@4",
            "again_new_password": "Secret123@4",
        },
        headers=headers,
    )

    assert resp.status_code == 200

    resp2 = await client.get("/api/users/me", headers=headers)
    data = resp2.json()
    username = data["username"]

    # try to login with old password
    resp3 = await client.post(
        "/auth/login", json={"username": username, "password": "Secret123@"}
    )
    data1 = resp3.json()
    assert resp3.status_code == 400
    assert "incorrect" in data1["detail"].lower()

    # try to login with new password
    resp4 = await client.post(
        "/auth/login", json={"username": username, "password": "Secret123@4"}
    )
    assert resp4.status_code == 200
    data2 = resp4.json()
    assert set(data2.keys()) == {"access_token", "refresh_token", "token_type"}
    assert data2["token_type"] == "bearer"
