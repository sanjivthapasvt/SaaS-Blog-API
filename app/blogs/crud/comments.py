from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.blogs.models import Blog, Comment


async def create_comment(
    session: AsyncSession,
    blog_id: int,
    content: str,
    commented_by: int,
    parent_id: int | None = None,
) -> Comment:
    """
    Create a comment on a blog post.

    Args:
        session: Database session
        blog_id: ID of the blog to comment on
        content: Comment content
        commented_by: ID of the user creating the comment
        parent_id: Optional ID of parent comment for replies

    Returns the created Comment instance.
    """
    if content.strip() == "":
        raise HTTPException(status_code=400, detail="The field cannot be empty")

    blog = await session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    # Validate parent comment if provided
    if parent_id is not None:
        parent_result = await session.execute(
            select(Comment).where(Comment.id == parent_id)
        )
        parent_comment = parent_result.scalars().first()
        if not parent_comment:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        if parent_comment.blog_id != blog_id:
            raise HTTPException(
                status_code=400, detail="Parent comment belongs to a different blog"
            )

    new_comment = Comment(
        blog_id=blog_id,
        content=content,
        commented_by=commented_by,
        parent_id=parent_id,
    )
    blog.comments_count += 1

    session.add(new_comment)
    session.add(blog)
    await session.commit()
    await session.refresh(new_comment)

    return new_comment


async def read_comments(blog_id: int, session: AsyncSession):
    """
    Retrieve all top-level comments for a given blog.
    Replies are loaded automatically via the relationship.

    Raises 404 if blog not found.

    Returns list of top-level Comment instances with nested replies.
    """
    if not await session.get(Blog, blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")

    # Get only top-level comments (parent_id is None)
    comments = await session.execute(
        select(Comment)
        .where(Comment.blog_id == blog_id, Comment.parent_id == None)
        .options(selectinload(Comment.replies).selectinload(Comment.replies))
        .order_by(Comment.created_at.desc())
    )
    return comments.scalars().all()


async def get_comment_replies(comment_id: int, session: AsyncSession):
    """
    Get all replies to a specific comment.

    Args:
        comment_id: ID of the parent comment
        session: Database session

    Returns list of reply Comment instances.
    """
    parent_comment = await session.get(Comment, comment_id)
    if not parent_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    replies = await session.execute(
        select(Comment)
        .where(Comment.parent_id == comment_id)
        .order_by(Comment.created_at.asc())
    )
    return replies.scalars().all()


async def update_comment(
    comment_id: int, content: str, session: AsyncSession, current_user: int
):
    """
    Update content of a comment owned by the current user.

    Raises 404 if comment not found, 403 if user is not the owner.

    Returns dict confirming success.
    """
    if content.strip() == "":
        raise HTTPException(status_code=400, detail="The field cannot be empty")

    raw_comment = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = raw_comment.scalars().first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if comment.commented_by != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of the comment"
        )

    comment.content = content
    comment.last_modified = datetime.now(timezone.utc)
    session.add(comment)
    await session.commit()

    return {"detail": "Successfully updated comment"}


async def delete_comment(comment_id: int, session: AsyncSession, current_user: int):
    """
    Delete a comment owned by the current user.

    Raises 404 if comment not found, 403 if user is not the owner.

    Returns dict confirming success.
    """
    raw_comment = await session.execute(select(Comment).where(Comment.id == comment_id))
    comment = raw_comment.scalars().first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.commented_by != current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of the comment"
        )
    blog = await session.get(Blog, comment.blog_id)
    if blog:
        blog.comments_count -= 1
        session.add(blog)
    await session.delete(comment)
    await session.commit()
    return {"detail": "Successfully deleted comment"}
