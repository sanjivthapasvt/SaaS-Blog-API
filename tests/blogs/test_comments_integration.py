import pytest
from httpx import AsyncClient

from tests.blogs.test_comments_crud import _create_blog
from tests.test_users import _auth_header


class TestCommentIntegration:
    """Test comment integration with other features"""

    @pytest.mark.asyncio
    async def test_complete_comment_workflow(self, client: AsyncClient):
        """Test complete comment workflow: create, read, update, delete"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        # 1. Create comment
        create_resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "Workflow test comment"},
            headers=headers,
        )
        assert create_resp.status_code == 200

        # 2. Read comment
        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        assert comments_resp.status_code == 200
        comments = comments_resp.json()
        assert len(comments) == 1
        comment_id = comments[0]["id"]

        # 3. Update comment
        update_resp = await client.patch(
            f"/api/comments/{comment_id}",
            json={"content": "Updated workflow comment"},
            headers=headers,
        )
        assert update_resp.status_code == 200

        # 4. Verify update
        updated_comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        updated_comments = updated_comments_resp.json()
        assert updated_comments[0]["content"] == "Updated workflow comment"

        # 5. Delete comment
        delete_resp = await client.delete(
            f"/api/comments/{comment_id}", headers=headers
        )
        assert delete_resp.status_code == 200

        # 6. Verify deletion
        final_comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        final_comments = final_comments_resp.json()
        assert len(final_comments) == 0

    @pytest.mark.asyncio
    async def test_multiple_users_commenting(self, client: AsyncClient):
        """Test multiple users commenting on same blog"""
        # Create blog
        blog_id, blog_author_headers = await _create_blog(client)

        # Create other users
        user1_headers = await _auth_header(client)
        user2_headers = await _auth_header(client)

        # Multiple users comment on the blog
        comments_data = [
            (blog_author_headers, "Author's own comment"),
            (user1_headers, "User1's comment"),
            (user2_headers, "User2's comment"),
        ]

        for headers, content in comments_data:
            resp = await client.post(
                f"/api/blogs/{blog_id}/comments",
                json={"content": content},
                headers=headers,
            )
            assert resp.status_code == 200

        # Verify all comments exist
        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comments = comments_resp.json()
        assert len(comments) == 3

        # Each user can only update/delete their own comment
        for comment in comments:
            comment_id = comment["id"]
            comment_content = comment["content"]

            # Determine which user owns this comment
            if "Author's" in comment_content:
                owner_headers = blog_author_headers
                non_owner_headers = user1_headers
            elif "User1's" in comment_content:
                owner_headers = user1_headers
                non_owner_headers = user2_headers
            else:  # User2's comment
                owner_headers = user2_headers
                non_owner_headers = blog_author_headers

            # Owner can update
            update_resp = await client.patch(
                f"/api/comments/{comment_id}",
                json={"content": f"Updated {comment_content}"},
                headers=owner_headers,
            )
            assert update_resp.status_code == 200

            # Non-owner cannot update
            update_resp2 = await client.patch(
                f"/api/comments/{comment_id}",
                json={"content": "Unauthorized update"},
                headers=non_owner_headers,
            )
            assert update_resp2.status_code in [403, 404]

    @pytest.mark.asyncio
    async def test_comments_after_blog_deletion(self, client: AsyncClient):
        """Test comment behavior when blog is deleted"""
        headers = await _auth_header(client)
        blog_id, blog_headers = await _create_blog(client)

        # Create comments
        for i in range(3):
            resp = await client.post(
                f"/api/blogs/{blog_id}/comments",
                json={"content": f"Comment {i}"},
                headers=headers,
            )
            assert resp.status_code == 200

        # Get comment IDs
        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comments = comments_resp.json()
        comment_ids = [comment["id"] for comment in comments]

        # Delete the blog
        delete_blog_resp = await client.delete(
            f"/api/blogs/{blog_id}", headers=blog_headers
        )
        assert delete_blog_resp.status_code == 200

        # Try to access comments - should return 404 for the blog
        comments_resp2 = await client.get(f"/api/blogs/{blog_id}/comments")
        assert comments_resp2.status_code == 404

        # Try to update/delete individual comments
        for comment_id in comment_ids:
            update_resp = await client.patch(
                f"/api/comments/{comment_id}",
                json={"content": "Update after blog deletion"},
                headers=headers,
            )
            # Should be 404
            assert update_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_comment_author_information(self, client: AsyncClient):
        """Test that comment includes correct author information"""
        headers = await _auth_header(client)
        blog_id, _ = await _create_blog(client)

        # Get user info
        user_resp = await client.get("/api/users/me", headers=headers)
        user_data = user_resp.json()
        user_id = user_data["id"]

        # Create comment
        resp = await client.post(
            f"/api/blogs/{blog_id}/comments",
            json={"content": "Test author information"},
            headers=headers,
        )
        assert resp.status_code == 200

        # Verify author information in comment
        comments_resp = await client.get(f"/api/blogs/{blog_id}/comments")
        comments = comments_resp.json()
        comment = comments[0]

        assert comment["commented_by"] == user_id
        assert comment["blog_id"] == blog_id
