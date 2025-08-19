import pytest
from httpx import AsyncClient


from tests.auth_utils import _create_user
from tests.blogs.test_blogs_validation_and_integration import validate_response
from tests.schema.global_schema import PaginatedResponse
from tests.schema.blog_and_comment_schema import BlogResponse

class TestBlogLikes:
    """Test blog like/unlike functionality"""

    @pytest.mark.asyncio
    async def test_liked_blogs_validation(self, client: AsyncClient):
        """Test liked blogs endpoint"""
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
        validated_blogs = validate_response(
            blogs_resp.json(), PaginatedResponse[BlogResponse]
        )
        blog_id = validated_blogs.data[0].id

        like_resp = await client.post(f"/api/blogs/{blog_id}/like", headers=headers)
        assert like_resp.status_code == 200
        assert "liked" in like_resp.json()["detail"]

        # Get liked blogs and validate
        liked_resp = await client.get("/api/blogs/liked", headers=headers)
        assert liked_resp.status_code == 200

        validated_liked = validate_response(
            liked_resp.json(), PaginatedResponse[BlogResponse]
        )
        assert validated_liked.total == 1
        assert len(validated_liked.data) == 1

        liked_blog = validated_liked.data[0]
        assert liked_blog.id == blog_id
        assert liked_blog.title == "Blog to Like"

    @pytest.mark.asyncio
    async def test_like_unlike_blog_flow(self, client: AsyncClient):
        """Test complete like/unlike flow """
        headers = await _create_user(client, "LikeFlowUser")
        
        # Create a blog
        create_resp = await client.post(
            "/api/blogs",
            data={
                "title": "Likeable Post",
                "content": "Please like this post",
            },
            headers=headers,
        )
        assert create_resp.status_code == 201
        
        # Get blog ID
        blogs_resp = await client.get("/api/blogs?search=Likeable")
        validated_blogs = validate_response(blogs_resp.json(), PaginatedResponse[BlogResponse])
        blog_id = validated_blogs.data[0].id
        
        # Like the blog
        like_resp = await client.post(f"/api/blogs/{blog_id}/like", headers=headers)
        assert like_resp.status_code == 200
        assert "added" in like_resp.json()["detail"].lower()
        
        # Verify blog appears in liked blogs
        liked_resp = await client.get("/api/blogs/liked", headers=headers)
        assert liked_resp.status_code == 200
        validated_liked = validate_response(liked_resp.json(), PaginatedResponse[BlogResponse])
        assert validated_liked.total == 1
        assert any(blog.id == blog_id for blog in validated_liked.data)
        
        # Unlike the blog
        unlike_resp = await client.post(f"/api/blogs/{blog_id}/like", headers=headers)
        assert unlike_resp.status_code == 200
        assert "removed" in unlike_resp.json()["detail"].lower()
        
        # Verify blog no longer in liked blogs
        liked_resp2 = await client.get("/api/blogs/liked", headers=headers)
        assert liked_resp2.status_code == 200
        validated_liked2 = validate_response(liked_resp2.json(), PaginatedResponse[BlogResponse])
        assert validated_liked2.total == 0

    @pytest.mark.asyncio
    async def test_like_nonexistent_blog(self, client: AsyncClient):
        """Test liking a non-existent blog"""
        headers = await _create_user(client, "LikeNonExistentUser")
        
        like_resp = await client.post("/api/blogs/99999/like", headers=headers)
        assert like_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_like_unauthorized(self, client: AsyncClient):
        """Test liking without authentication"""
        like_resp = await client.post("/api/blogs/1/like")
        assert like_resp.status_code == 403

    @pytest.mark.asyncio
    async def test_get_liked_blogs_empty(self, client: AsyncClient):
        """Test getting liked blogs when user hasn't liked any"""
        headers = await _create_user(client, "NoLikesUser")
        
        resp = await client.get("/api/blogs/liked", headers=headers)
        assert resp.status_code == 200
        
        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        assert validated_data.total == 0
        assert isinstance(validated_data.data, list)

    @pytest.mark.asyncio
    async def test_get_liked_blogs_with_pagination(self, client: AsyncClient):
        """Test liked blogs pagination"""
        headers = await _create_user(client, "LikesPaginationUser")
        
        # Create and like multiple blogs
        blog_ids = []
        for i in range(5):
            create_resp = await client.post(
                "/api/blogs",
                data={
                    "title": f"Like Blog{i}",
                    "content": f"Content {i}",
                },
                headers=headers,
            )
            assert create_resp.status_code == 201
            
            # Get the blog ID from the created blog using validation
            blogs_resp = await client.get(f"/api/blogs?search=Like%Blog{i}")
            validated_blogs = validate_response(blogs_resp.json(), PaginatedResponse[BlogResponse])
            blog_id = validated_blogs.data[0].id
            blog_ids.append(blog_id)
            
            # Like the blog
            await client.post(f"/api/blogs/{blog_id}/like", headers=headers)
        
        # Test pagination with validation
        resp = await client.get("/api/blogs/liked?limit=3", headers=headers)
        assert resp.status_code == 200
        validated_data = validate_response(resp.json(), PaginatedResponse[BlogResponse])
        assert validated_data.total == 5
        assert validated_data.limit == 3
        assert len(validated_data.data) == 3
