from datetime import datetime, timezone

from fastapi import HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import  select

from app.blogs.models import Blog, Comment


async def create_comment(
    session: AsyncSession, blog_id: int, content: str, commented_by: int
) -> Comment:
    """
    Create a comment on a blog post.

    Returns the created Comment instance.
    """
    if content.strip() == "":
        raise HTTPException(status_code=400, detail="The field cannot be empty")

    blog = await session.get(Blog, blog_id)
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    new_comment = Comment(blog_id=blog_id, content=content, commented_by=commented_by)

    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)

    return new_comment


async def read_comments(blog_id: int, session: AsyncSession):
    """
    Retrieve all comments for a given blog.

    Raises 404 if blog not found.

    Returns list of Comment instances.
    """
    if not await session.get(Blog, blog_id):
        raise HTTPException(status_code=404, detail="Blog not found")

    comments = await session.execute(select(Comment).where(Comment.blog_id == blog_id))
    return comments.scalars().all()


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

    await session.delete(comment)
    await session.commit()
    return {"detail": "Successfully deleted comment"}
