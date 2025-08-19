from typing import Any, Type, TypeVar
import pytest
from httpx import AsyncClient
from pydantic import BaseModel, TypeAdapter, ValidationError


from tests.auth_utils import _create_user
from tests.schema.global_schema import PaginatedResponse
from tests.schema.blog_and_comment_schema import BlogResponse, BlogContentResponse

T = TypeVar("T", bound=BaseModel)


def validate_response(data: Any, schema: Type[T]) -> T:
    """
    Validate response against the given Pydantic schema.
    Collects all validation errors if present.
    """
    adapter = TypeAdapter(schema)
    try:
        return adapter.validate_python(data)
    except ValidationError as e:
        # Re-raise with all collected issues for pytest readability
        raise AssertionError(
            f"Response validation failed for {schema.__name__}:\n{e.errors()}"
        ) from e



class TestBlogValidation:
    """Test blog input validation and edge cases """

    @pytest.mark.asyncio
    async def test_create_blog_empty_title(self, client: AsyncClient):
        """Test blog creation with empty title"""
        headers = await _create_user(client, "EmptyTitleUser")
        
        resp = await client.post(
            "/api/blogs",
            data={
                "title": "",
                "content": "Content without title",
            },
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_blog_empty_content(self, client: AsyncClient):
        """Test blog creation with empty content"""
        headers = await _create_user(client, "EmptyContentUser")
        
        resp = await client.post(
            "/api/blogs",
            data={
                "title": "Title without content",
                "content": "",
            },
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_blog_very_long_title(self, client: AsyncClient):
        """Test blog creation with very long title"""
        headers = await _create_user(client, "LongTitleUser")
        
        long_title = "x" * 1000  # Very long title
        resp = await client.post(
            "/api/blogs",
            data={
                "title": long_title,
                "content": "Content with very long title",
            },
            headers=headers,
        )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_blog_id_parameter(self, client: AsyncClient):
        """Test endpoints with invalid blog ID parameters"""
        headers = await _create_user(client, "InvalidIdUser")
        
        # Test with non-numeric ID
        resp = await client.get("/api/blogs/invalid")
        assert resp.status_code == 422
        
        # Test with negative ID
        resp = await client.get("/api/blogs/-1")
        assert resp.status_code == 404
        
        # Test like with invalid ID
        resp = await client.post("/api/blogs/invalid/like", headers=headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_error_response_validation(self, client: AsyncClient):
        """Test error responses have correct structure"""
        # Test validation error (422)
        headers = await _create_user(client, "ErrorValidationUser")

        resp = await client.post(
            "/api/blogs",
            data={"title": "Missing Content"},  # Missing required content field
            headers=headers,
        )
        assert resp.status_code == 422

        error_data = resp.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)

        # Test not found (404)
        resp = await client.get("/api/blogs/99999")
        assert resp.status_code == 404

        # Test unauthorized (403)
        resp = await client.post(
            "/api/blogs", data={"title": "Test", "content": "Test"}
        )
        assert resp.status_code == 403


class TestBlogIntegration:
    """Integration tests combining multiple features """

    @pytest.mark.asyncio
    async def test_blog_workflow_complete(self, client: AsyncClient):
        """Test complete blog workflow with validation: create, read, update, like, delete"""
        headers = await _create_user(client, "WorkflowUser")
        
        # 1. Create blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Workflow Test Blog",
                "content": "Testing complete workflow",
                "tags": "#workflow#test"
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        
        # 2. Find and read blog
        blogs_resp = await client.get("/api/blogs?search=Workflow")
        assert blogs_resp.status_code == 200
        validated_blogs = validate_response(blogs_resp.json(), PaginatedResponse[BlogResponse])
        blog_id = validated_blogs.data[0].id
        
        get_resp = await client.get(f"/api/blogs/{blog_id}")
        assert get_resp.status_code == 200
        validated_blog = validate_response(get_resp.json(), BlogContentResponse)
        
        # 3. Update blog
        update_resp = await client.patch(
            f"/api/blogs/{blog_id}",
            data={"title": "Updated Workflow Blog"},
            headers=headers,
        )
        assert update_resp.status_code == 200
        
        # 4. Like blog
        like_resp = await client.post(f"/api/blogs/{blog_id}/like", headers=headers)
        assert like_resp.status_code == 200
        
        # 5. Verify in liked blogs
        liked_resp = await client.get("/api/blogs/liked", headers=headers)
        assert liked_resp.status_code == 200
        validated_liked = validate_response(liked_resp.json(), PaginatedResponse[BlogResponse])
        assert validated_liked.total == 1
        
        # 6. Delete blog
        delete_resp = await client.delete(f"/api/blogs/{blog_id}", headers=headers)
        assert delete_resp.status_code == 200
        
        # 7. Verify deletion
        get_resp = await client.get(f"/api/blogs/{blog_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_multiple_users_blog_interaction(self, client: AsyncClient):
        """Test blog interactions between multiple users """
        # Create two users
        headers1 = await _create_user(client, "User1")
        headers2 = await _create_user(client, "User2")
        
        # User1 creates a blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "User1's Blog",
                "content": "Content by User1",
            },
            headers=headers1,
        )
        assert create_resp.status_code == 201
        
        # Get blog ID using validation
        blogs_resp = await client.get("/api/blogs?search=User1")
        validated_blogs = validate_response(blogs_resp.json(), PaginatedResponse[BlogResponse])
        blog_id = validated_blogs.data[0].id
        
        # User2 can read the blog
        read_resp = await client.get(f"/api/blogs/{blog_id}")
        assert read_resp.status_code == 200
        validated_blog = validate_response(read_resp.json(), BlogContentResponse)
        
        # User2 can like the blog
        like_resp = await client.post(f"/api/blogs/{blog_id}/like", headers=headers2)
        assert like_resp.status_code == 200
        
        # User2 cannot update User1's blog
        update_resp = await client.patch(
            f"/api/blogs/{blog_id}",
            data={"title": "Hacked by User2"},
            headers=headers2,
        )
        assert update_resp.status_code == 403
        
        # User2 cannot delete User1's blog
        delete_resp = await client.delete(f"/api/blogs/{blog_id}", headers=headers2)
        assert delete_resp.status_code == 403