from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.test_users import _auth_header


async def _create_blog(client: AsyncClient, headers=None) -> tuple[int, dict[str, str]]:
    """Create a blog and return blog_id and headers"""
    if headers is None:
        headers = await _auth_header(client)

    resp = await client.post(
        "/api/blogs",
        data={
            "title": f"Test Blog {uuid4().hex[:6]}",
            "content": "Test blog content",
            "tags": "#test#blog",
        },
        headers=headers,
    )
    assert resp.status_code == 201

    # Get blog ID from user's blogs
    resp2 = await client.get("/api/users/me/blogs", headers=headers)
    assert resp2.status_code == 200
    page = resp2.json()
    blog_id = page["data"][0]["id"]

    return blog_id, headers


class TestCommentBasics:
    """Test basic comment functionality"""

    @pytest.mark.asyncio
    async def test_get_comments_empty_blog(self, client: AsyncClient):
        """Test getting comments from a blog with no comments"""
        blog_id, _ = await _create_blog(client)

        resp = await client.get(f"/api/blogs/{blog_id}/comments")
        assert resp.status_code == 200

        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_comments_nonexistent_blog(self, client: AsyncClient):
        """Test getting comments from non-existent blog"""
        resp = await client.get("/api/blogs/99999/comments")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_comments_invalid_blog_id(self, client: AsyncClient):
        """Test getting comments with invalid blog ID"""
        resp = await client.get("/api/blogs/invalid/comments")
        assert resp.status_code == 422


class TestCommentCRUD:
    """Test Create, Read, Update, Delete operations for comments"""

    @pytest.mark.asyncio
    async def test_create_comment_success(self, client: AsyncClient):
        """Test successful comment creation"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "This is a test comment"},
            headers=headers,
        )
        assert resp.status_code == 200

        # Verify comment was created
        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        assert comments_resp.status_code == 200

        comments = comments_resp.json()
        assert len(comments) == 1
        assert comments[0]["content"] == "This is a test comment"

    @pytest.mark.asyncio
    async def test_create_comment_unauthorized(self, client: AsyncClient):
        """Test comment creation without authentication"""
        blog_id, _ = await _create_blog(client)

        resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "Unauthorized comment"},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_create_comment_nonexistent_blog(self, client: AsyncClient):
        """Test comment creation on non-existent blog"""
        headers = await _auth_header(client)

        resp = await client.post(
            "/api/blogs/99999/comments",
            json={"content": "Comment on non-existent blog"},
            headers=headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_comment_empty_content(self, client: AsyncClient):
        """Test comment creation with empty content"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": ""},
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_comment_missing_content(self, client: AsyncClient):
        """Test comment creation with missing content field"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={},
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_multiple_comments(self, client: AsyncClient):
        """Test creating multiple comments on same blog"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        comments_content = ["First comment", "Second comment", "Third comment"]

        # Create multiple comments
        for content in comments_content:
            resp = await client.post(
                f"/api/blogs/{blog_id}/comments",
                json={"content": content},
                headers=headers,
            )
            assert resp.status_code == 200

        # Verify all comments exist
        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        assert comments_resp.status_code == 200

        comments = comments_resp.json()
        assert len(comments) == 3

        comment_texts = [comment["content"] for comment in comments]
        for expected_content in comments_content:
            assert expected_content in comment_texts

    @pytest.mark.asyncio
    async def test_update_comment_success(self, client: AsyncClient):
        """Test successful comment update"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        # Create comment
        create_resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "Original comment"},
            headers=headers,
        )
        assert create_resp.status_code == 200

        # Get comment ID
        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comment_id = comments_resp.json()[0]["id"]

        # Update comment
        update_resp = await client.patch(
            f"/api/comments/{comment_id}",
            json={"content": "Updated comment content"},
            headers=headers,
        )
        assert update_resp.status_code == 200

        # Verify update
        updated_comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        updated_comments = updated_comments_resp.json()
        assert updated_comments[0]["content"] == "Updated comment content"

    @pytest.mark.asyncio
    async def test_update_comment_unauthorized(self, client: AsyncClient):
        """Test comment update without authentication"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        # Create comment
        create_resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "Original comment"},
            headers=headers,
        )
        assert create_resp.status_code == 200

        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comment_id = comments_resp.json()[0]["id"]

        # Try to update without auth
        update_resp = await client.patch(
            f"/api/comments/{comment_id}",
            json={"content": "Unauthorized update"},
        )
        assert update_resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_comment_by_different_user(self, client: AsyncClient):
        """Test that users cannot update other users' comments"""
        # User 1 creates comment
        user1_headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        create_resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "User1's comment"},
            headers=user1_headers,
        )
        assert create_resp.status_code == 200

        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comment_id = comments_resp.json()[0]["id"]

        # User 2 tries to update User1's comment
        user2_headers = await _auth_header(client)
        update_resp = await client.patch(
            f"/api/comments/{comment_id}",
            json={"content": "Hacked by User2"},
            headers=user2_headers,
        )
        assert update_resp.status_code == 403

    @pytest.mark.asyncio
    async def test_update_nonexistent_comment(self, client: AsyncClient):
        """Test updating non-existent comment"""
        headers = await _auth_header(client)

        resp = await client.patch(
            "/api/comments/99999",
            json={"content": "Update non-existent"},
            headers=headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_update_comment_empty_content(self, client: AsyncClient):
        """Test updating comment with empty content"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        # Create comment
        create_resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "Original comment"},
            headers=headers,
        )
        assert create_resp.status_code == 200

        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comment_id = comments_resp.json()[0]["id"]

        # Try to update with empty content
        update_resp = await client.patch(
            f"/api/comments/{comment_id}",
            json={"content": ""},
            headers=headers,
        )
        assert update_resp.status_code == 422

    @pytest.mark.asyncio
    async def test_delete_comment_success(self, client: AsyncClient):
        """Test successful comment deletion"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        # Create comment
        create_resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "Comment to delete"},
            headers=headers,
        )
        assert create_resp.status_code == 200

        # Get comment ID
        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comment_id = comments_resp.json()[0]["id"]

        # Delete comment
        delete_resp = await client.delete(
            f"/api/comments/{comment_id}", headers=headers
        )
        assert delete_resp.status_code == 200

        # Verify deletion
        verify_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        assert verify_resp.status_code == 200
        comments = verify_resp.json()
        assert len(comments) == 0

    @pytest.mark.asyncio
    async def test_delete_comment_unauthorized(self, client: AsyncClient):
        """Test comment deletion without authentication"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        # Create comment
        create_resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "Comment to delete"},
            headers=headers,
        )
        assert create_resp.status_code == 200

        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comment_id = comments_resp.json()[0]["id"]

        # Try to delete without auth
        delete_resp = await client.delete(f"/api/comments/{comment_id}")
        assert delete_resp.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_comment_by_different_user(self, client: AsyncClient):
        """Test that users cannot delete other users' comments"""
        # User1 creates comment
        user1_headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        create_resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "User1's comment"},
            headers=user1_headers,
        )
        assert create_resp.status_code == 200

        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comment_id = comments_resp.json()[0]["id"]

        # User2 tries to delete User1's comment
        user2_headers = await _auth_header(client)
        delete_resp = await client.delete(
            f"/api/comments/{comment_id}", headers=user2_headers
        )
        assert delete_resp.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_nonexistent_comment(self, client: AsyncClient):
        """Test deleting non-existent comment"""
        headers = await _auth_header(client)

        resp = await client.delete("/api/comments/99999", headers=headers)
        assert resp.status_code == 404
