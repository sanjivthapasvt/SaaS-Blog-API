import os
import tempfile
from datetime import datetime

import pytest
from httpx import AsyncClient

from tests.blogs.test_blogs_validation_and_integration import validate_response
from tests.schema.blog_and_comment_schema import (BlogContentResponse,
                                                  BlogResponse)
from tests.schema.global_schema import PaginatedResponse
from tests.utils.auth_utils import _create_user


class TestBlogCRUD:
    """Test CRUD operations"""

    @pytest.mark.asyncio
    async def test_get_all_blogs_empty(self, client: AsyncClient):
        """Test getting all blogs when database is empty"""
        resp = await client.get("/api/blogs")
        assert resp.status_code == 200

        # Validate response structure
        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])

        assert validated_data.total == 0
        assert validated_data.limit == 10
        assert validated_data.offset == 0
        assert len(validated_data.data) == 0

    @pytest.mark.asyncio
    async def test_get_all_blogs_with_pagination(self, client: AsyncClient):
        """Test pagination parameters"""
        headers = await _create_user(client, "PaginationUser")

        # Create multiple blogs (up to rate limit of 10 per minute)
        for i in range(10):
            await client.post(
                "/api/blogs",
                data={
                    "title": f"Pagination Blog {i:02d}",
                    "content": f"Content for blog {i}",
                    "tags": f"#blog{i}#pagination",
                },
                headers=headers,
            )

        # Test default pagination
        resp = await client.get("/api/blogs?search=Pagination")
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
            assert blog.thumbnail_url is None

        # Test custom pagination
        resp = await client.get("/api/blogs?search=Pagination&limit=5&offset=5")
        assert resp.status_code == 200

        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        assert validated_data.total == 10
        assert validated_data.limit == 5
        assert validated_data.offset == 5
        assert len(validated_data.data) == 5

    @pytest.mark.asyncio
    async def test_get_all_blogs_with_search(self, client: AsyncClient):
        """Test search functionality"""
        headers = await _create_user(client, "SearchUser")

        # Create blogs with different titles
        blogs = [
            {
                "title": "Python FastAPI",
                "content": "Learn FastAPI",
                "tags": "#python#fastapi",
            },
            {
                "title": "React Components",
                "content": "React tutorial",
                "tags": "#react#components",
            },
            {
                "title": "FastAPI Advanced Features",
                "content": "Advanced FastAPI",
                "tags": "#fastapi#advanced",
            },
        ]

        for blog in blogs:
            await client.post("/api/blogs", data=blog, headers=headers)

        # Search for "FastAPI" with validation
        resp = await client.get("/api/blogs?search=FastAPI")
        assert resp.status_code == 200

        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        assert validated_data.total == 2

        # Search for "React" with validation
        resp = await client.get("/api/blogs?search=React")
        assert resp.status_code == 200

        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        assert validated_data.total == 1
        assert "React" in validated_data.data[0].title

    @pytest.mark.asyncio
    async def test_create_blog_success(self, client: AsyncClient):
        """Test successful blog creation"""
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

        # Fetch the created blog and validate it
        blogs_resp = await client.get("/api/blogs?search=Created")
        assert blogs_resp.status_code == 200

        validated_blogs = validate_response(
            blogs_resp.json(), PaginatedResponse[BlogResponse]
        )
        assert validated_blogs.total == 1

        blog = validated_blogs.data[0]
        assert blog.title == "Created Blog"
        assert isinstance(blog.id, int)
        assert isinstance(blog.author, int)
        assert isinstance(blog.created_at, datetime)
        assert blog.tags == ["blog", "created", "test"]

    @pytest.mark.asyncio
    async def test_create_blog_with_thumbnail(self, client: AsyncClient):
        """Test blog creation with thumbnail upload and validation"""
        headers = await _create_user(client, "ThumbnailUser")

        # Create a temporary image file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_file.write(b"fake image data")
            tmp_file.flush()

            with open(tmp_file.name, "rb") as f:
                resp = await client.post(
                    "/api/blogs",
                    data={
                        "title": "Blog with Thumbnail",
                        "content": "This blog has a thumbnail",
                        "tags": "#thumbnail#image",
                    },
                    files={"thumbnail": ("test.png", f, "image/png")},
                    headers=headers,
                )

        # Clean up
        os.unlink(tmp_file.name)

        assert resp.status_code == 201

        # Verify the blog was created with thumbnail using validation
        blogs_resp = await client.get("/api/blogs?search=Thumbnail")
        assert blogs_resp.status_code == 200

        validated_data = validate_response(
            blogs_resp.json(), PaginatedResponse[BlogResponse]
        )
        assert validated_data.total == 1

    @pytest.mark.asyncio
    async def test_create_blog_unauthorized(self, client: AsyncClient):
        """Test blog creation without authentication"""
        resp = await client.post(
            "/api/blogs",
            data={
                "title": "Created Blog",
                "content": "This blog has been created",
                "tags": "#blog#created#test",
            },
        )

        assert resp.status_code == 401
        assert "not authenticated" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_blog_invalid_data(self, client: AsyncClient):
        """Test blog creation with invalid data"""
        headers = await _create_user(client, "InvalidDataUser")

        # Test missing required fields
        resp = await client.post(
            "/api/blogs",
            data={"title": "Missing Content"},
            headers=headers,
        )
        assert resp.status_code == 422

        # Validate error response
        error_data = resp.json()
        assert "detail" in error_data
        assert isinstance(error_data["detail"], list)

        # Test missing title
        resp = await client.post(
            "/api/blogs",
            data={"content": "Missing Title"},
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_get_specific_blog(self, client: AsyncClient):
        """Test getting specific blog"""
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
        validated_blogs = validate_response(
            blogs_resp.json(), PaginatedResponse[BlogResponse]
        )
        blog_id = validated_blogs.data[0].id

        # Get specific blog and validate content response
        resp = await client.get(f"/api/blogs/{blog_id}")
        assert resp.status_code == 200

        validated_blog = validate_response(resp.json(), BlogContentResponse)
        assert validated_blog.title == "Specific Created Blog"
        assert validated_blog.content == "This is the full content of the blog"
        assert isinstance(validated_blog.author, int)
        assert isinstance(validated_blog.created_at, datetime)

    @pytest.mark.asyncio
    async def test_get_specific_blog_not_found(self, client: AsyncClient):
        """Test getting a non-existent blog"""
        resp = await client.get("/api/blogs/99999")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_blog_success(self, client: AsyncClient):
        """Test successful blog update with validation"""
        headers = await _create_user(client, "UpdateBlogUser")

        # Create a blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Original Title",
                "content": "Original content",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201

        # Get blog ID
        blogs_resp = await client.get("/api/blogs?search=Original")
        validated_blogs = validate_response(
            blogs_resp.json(), PaginatedResponse[BlogResponse]
        )
        blog_id = validated_blogs.data[0].id

        # Update blog
        update_resp = await client.patch(
            f"/api/blogs/{blog_id}",
            data={
                "title": "Updated Title",
                "content": "Updated content",
            },
            headers=headers,
        )
        assert update_resp.status_code == 200

        # Verify update
        blog_resp = await client.get(f"/api/blogs/{blog_id}")
        validated_blog = validate_response(blog_resp.json(), BlogContentResponse)
        assert validated_blog.title == "Updated Title"
        assert validated_blog.content == "Updated content"

    @pytest.mark.asyncio
    async def test_update_blog_with_thumbnail(self, client: AsyncClient):
        """Test blog update with thumbnail and validation"""
        headers = await _create_user(client, "UpdateThumbnailUser")

        # Create a blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Blog for Thumbnail Update",
                "content": "Content before thumbnail update",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201

        # Get blog ID using validation
        blogs_resp = await client.get("/api/blogs?search=Thumbnail%Update")
        validated_blogs = validate_response(
            blogs_resp.json(), PaginatedResponse[BlogResponse]
        )
        blog_id = validated_blogs.data[0].id

        # Update with thumbnail
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            tmp_file.write(b"updated image data")
            tmp_file.flush()

            with open(tmp_file.name, "rb") as f:
                update_resp = await client.patch(
                    f"/api/blogs/{blog_id}",
                    data={"title": "Updated with Thumbnail"},
                    files={"thumbnail": ("updated.png", f, "image/png")},
                    headers=headers,
                )

        os.unlink(tmp_file.name)
        assert update_resp.status_code == 200

    @pytest.mark.asyncio
    async def test_update_blog_unauthorized(self, client: AsyncClient):
        """Test blog update by non-owner"""
        # Create two users
        headers1 = await _create_user(client, "BlogOwner")
        headers2 = await _create_user(client, "NotOwner")

        create_resp = await client.post(
            "/api/blogs",
            data={"title": "Owner's Blog", "content": "Owner's content"},
            headers=headers1,
        )
        assert create_resp.status_code == 201

        # Get blog ID using validation
        blogs_resp = await client.get("/api/blogs?search=Owner")
        validated_blogs = validate_response(
            blogs_resp.json(), PaginatedResponse[BlogResponse]
        )
        blog_id = validated_blogs.data[0].id

        # Try to update with different user
        update_resp = await client.patch(
            f"/api/blogs/{blog_id}",
            data={"title": "Hacked Title"},
            headers=headers2,
        )
        assert update_resp.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_blog_success(self, client: AsyncClient):
        """Test successful blog deletion with validation"""
        headers = await _create_user(client, "DeleteBlogUser")

        # Create a blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Blog to Delete",
                "content": "This blog will be deleted",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201

        # Get blog ID
        blogs_resp = await client.get("/api/blogs?search=Delete")
        validated_blogs = validate_response(
            blogs_resp.json(), PaginatedResponse[BlogResponse]
        )
        blog_id = validated_blogs.data[0].id

        # Delete blog
        delete_resp = await client.delete(f"/api/blogs/{blog_id}", headers=headers)
        assert delete_resp.status_code == 200

        # Verify deletion
        get_resp = await client.get(f"/api/blogs/{blog_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_blog_unauthorized(self, client: AsyncClient):
        """Test blog deletion by non-owner"""
        headers1 = await _create_user(client, "BlogOwnerDelete")
        headers2 = await _create_user(client, "NotOwnerDelete")

        # Create blog
        create_resp = await client.post(
            "/api/blogs",
            data={"title": "Protected Blog", "content": "Cannot be deleted by others"},
            headers=headers1,
        )
        assert create_resp.status_code == 201

        # Get blog ID using validation
        blogs_resp = await client.get("/api/blogs?search=Protected")
        validated_blogs = validate_response(
            blogs_resp.json(), PaginatedResponse[BlogResponse]
        )
        blog_id = validated_blogs.data[0].id

        # Try to delete with different user
        delete_resp = await client.delete(f"/api/blogs/{blog_id}", headers=headers2)
        assert delete_resp.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_nonexistent_blog(self, client: AsyncClient):
        """Test deleting a non-existent blog"""
        headers = await _create_user(client, "DeleteNonExistentUser")

        delete_resp = await client.delete("/api/blogs/99999", headers=headers)
        assert delete_resp.status_code == 404
