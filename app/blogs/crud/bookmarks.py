import asyncio

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.blogs.models import Blog
from app.users.models import BookMark, User


async def add_blog_to_bookmark(
    session: AsyncSession,
    user_id: int,
    blog_id: int,
):
    user, blog = await asyncio.gather(
        session.get(User, user_id), session.get(Blog, blog_id)
    )
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not blog:
        raise HTTPException(status_code=404, detail="Blog not found")

    bookmark = await session.execute(
        select(BookMark).where(
            (BookMark.blog_id == blog_id) & (BookMark.user_id == user_id)
        )
    )
    existing_bookmarks = bookmark.scalars().first()
    if existing_bookmarks:
        await session.delete(existing_bookmarks)
        await session.commit()
        return {"detail": "Successfully removed from bookmark"}

    new_bookmark = BookMark(user_id=user_id, blog_id=blog_id)
    session.add(new_bookmark)
    await session.commit()
    return {"detail": "Successfully added to bookmark"}
