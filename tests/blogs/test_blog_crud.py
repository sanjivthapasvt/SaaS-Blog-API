from typing import Any, Type, TypeVar
import pytest
from httpx import AsyncClient
from pydantic import BaseModel, TypeAdapter, ValidationError
from datetime import datetime

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
        
        
class TestBlogCRUD:
    """Test CRUD operations with Pydantic response validation"""

    @pytest.mark.asyncio
    async def test_get_all_blogs_empty(self, client: AsyncClient):
        """Test getting all blogs when database is empty with response validation"""
        resp = await client.get("/api/blogs")
        assert resp.status_code == 200
        
        # Validate response structure
        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        
        assert validated_data.total == 0
        assert validated_data.limit == 10
        assert validated_data.offset == 0
        assert len(validated_data.data) == 0

    @pytest.mark.asyncio
    async def test_create_blog(self, client: AsyncClient):
        """Test blog creation with response validation"""
        headers = await _create_user(client, "BlogCreator")

        resp = await client.post(
            "/api/blogs",
            data={
                "title": "Created Blog",
                "content": "This blog has been created",
                "tags": "#blog#created#test",
            },
            headers=headers,
        )
        
        assert resp.status_code == 201
        assert "successfull" in resp.json()["detail"].lower()
        
        # fetch the created blog and validate its structure
        blogs_resp = await client.get("/api/blogs?search=Created")
        assert blogs_resp.status_code == 200
        
        validated_blogs = validate_response(blogs_resp.json(), PaginatedResponse[BlogResponse])
        assert validated_blogs.total == 1
        
        blog = validated_blogs.data[0]
        assert blog.title == "Created Blog"
        assert isinstance(blog.id, int)
        assert isinstance(blog.author, int)
        assert isinstance(blog.created_at, datetime)
        assert blog.tags == ["blog", "created", "test"]

    @pytest.mark.asyncio
    async def test_get_specific_blog(self, client: AsyncClient):
        """Test getting specific blog with content validation"""
        headers = await _create_user(client, "SpecificBlogUser")
        
        # Create a blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Specific Created Blog",
                "content": "This is the full content of the blog",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        
        # Get blog ID
        blogs_resp = await client.get("/api/blogs?search=Specific%Created")
        validated_blogs = validate_response(blogs_resp.json(), PaginatedResponse[BlogResponse])
        blog_id = validated_blogs.data[0].id
        
        # Get specific blog and validate content response
        resp = await client.get(f"/api/blogs/{blog_id}")
        assert resp.status_code == 200
        
        validated_blog = validate_response(resp.json(), BlogContentResponse)
        assert validated_blog.id == blog_id
        assert validated_blog.title == "Specific Created Blog"
        assert validated_blog.content == "This is the full content of the blog"
        assert isinstance(validated_blog.author, int)
        assert isinstance(validated_blog.created_at, datetime)

    @pytest.mark.asyncio
    async def test_pagination_response(self, client: AsyncClient):
        """Test pagination with response validation"""
        headers = await _create_user(client, "PaginationValidationUser")
        
        # Create multiple blogs upto 10 cause I have set limit on creation to 10 blogs per min per user
        for i in range(10):
            await client.post(
                "/api/blogs",
                data={
                    "title": f"Pagination Blog {i:02d}",
                    "content": f"Content {i}",
                    "tags": f"#blog{i}#pagination"
                },
                headers=headers,
            )

        # Test default pagination
        resp = await client.get("/api/blogs?search=Pagination%Blog")
        assert resp.status_code == 200
        
        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        assert validated_data.total == 10
        assert validated_data.limit == 10
        assert validated_data.offset == 0
        assert len(validated_data.data) == 10
        
        # Validate each blog in the response
        for blog in validated_data.data:
            assert isinstance(blog.id, int)
            assert isinstance(blog.title, str)
            assert blog.title.startswith("Pagination Blog")
            assert isinstance(blog.author, int)
            assert isinstance(blog.tags, list)
            assert isinstance(blog.created_at, datetime)
            # thumbnail_url should be None
            assert blog.thumbnail_url is None

        # Test custom pagination
        resp = await client.get("/api/blogs?search=Pagination%Blog&limit=10&offset=5")
        assert resp.status_code == 200
        
        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        assert validated_data.total == 10
        assert validated_data.limit == 10
        assert validated_data.offset == 5
        assert len(validated_data.data) == 5

    @pytest.mark.asyncio
    async def test_liked_blogs_validation(self, client: AsyncClient):
        """Test liked blogs endpoint """
        headers = await _create_user(client, "LikedTestUser")
        
        # Create and like a blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Blog to Like",
                "content": "Content for testing",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        
        # Get blog ID and like it
        blogs_resp = await client.get("/api/blogs?search=Blog%to%Like")
        validated_blogs = validate_response(blogs_resp.json(), PaginatedResponse[BlogResponse])
        blog_id = validated_blogs.data[0].id
        
        like_resp = await client.post(f"/api/blogs/{blog_id}/like", headers=headers)
        assert like_resp.status_code == 200
        assert "liked" in like_resp.json()["detail"]
        
        # Get liked blogs and validate
        liked_resp = await client.get("/api/blogs/liked", headers=headers)
        assert liked_resp.status_code == 200
        
        validated_liked = validate_response(liked_resp.json(), PaginatedResponse[BlogResponse])
        assert validated_liked.total == 1
        assert len(validated_liked.data) == 1
        
        liked_blog = validated_liked.data[0]
        assert liked_blog.id == blog_id
        assert liked_blog.title == "Blog to Like"

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
        resp = await client.post("/api/blogs", data={"title": "Test", "content": "Test"})
        assert resp.status_code == 403
