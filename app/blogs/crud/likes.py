import asyncio
from typing import List

from aiosqlite import IntegrityError
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import and_, col, delete, exists, func, select

from app.blogs.models import Blog, BlogTagLink, Tag
from app.models.blog_like_link import BlogLikeLink
from app.notifications.models import Notification, NotificationType
from app.notifications.service import create_notification
from app.users.schema import CurrentUserRead


async def like_unlike_blog(
    session: AsyncSession,
    blog_id: int,
    current_user: CurrentUserRead,
    request: Request | None = None,
):
    """
    Toggle like/unlike status for a blog by the current user.

    Raises 404 if blog not found.

    Returns dict with action result message.
    """

    result = await session.execute(
        select(BlogLikeLink).where(
            (BlogLikeLink.blog_id == blog_id)
            & (BlogLikeLink.user_id == current_user.id)
        )
    )

    existing_like = result.scalars().first()

    if existing_like:
        blog = await session.get(Blog, blog_id)

        if not blog:
            raise HTTPException(status_code=404, detail="Blog doesn't exist")

        await session.delete(existing_like)
        # Delete notification if not self-like
        if current_user.id != blog.author:
            await session.execute(
                delete(Notification).where(
                    and_(
                        Notification.owner_id == blog.author,
                        Notification.blog_id == blog.id,
                        Notification.notification_type == NotificationType.LIKE,
                        Notification.triggered_by_user_id == current_user.id,
                    )
                )
            )
        await session.commit()
        return {"detail": "removed from liked blogs"}

    try:
        # get blog info for notification
        blog = await session.get(Blog, blog_id)

        if not blog:
            raise HTTPException(status_code=404, detail="Blog doesn't exist")

        # create like link
        new_link = BlogLikeLink(blog_id=blog_id, user_id=current_user.id)
        session.add(new_link)
        await session.commit()

        # create notification only if not self-like
        if current_user.id != blog.author:
            await create_notification(
                session=session,
                owner_id=blog.author,
                triggered_by_user_id=current_user.id,
                blog_id=blog.id,
                notification_type=NotificationType.LIKE,
                message=f"{current_user.full_name} liked your blog {blog.title}",
                request=request,
            )
        return {"detail": "added to liked blogs"}

    except IntegrityError:
        # race condition: like was created by another request
        await session.rollback()
        return {"detail": "already liked"}

async def get_liked_blogs(
    session: AsyncSession,
    search: str | None,
    limit: int,
    offset: int,
    user_id: int,
    tags: List[str] | None,
):
    """
    Retrieve paginated blogs liked by a user, optionally filtered by a search term.

    Returns a dict with total count, pagination info, and blog data.
    """

    base_query = (
        select(Blog)
        .join(BlogLikeLink, Blog.id == BlogLikeLink.blog_id)  # type: ignore
        .where(BlogLikeLink.user_id == user_id)
    )

    conditions = []

    if search:
        search_term = f"%{search.lower()}%"
        conditions.append(func.lower(Blog.title).like(search_term))

    # Tag filtering
    if tags:
        # Create a subquery that checks if a blog has all required tags
        tag_subquery = (
            select(BlogTagLink.blog_id)
            .join(Tag, BlogTagLink.tag_id == Tag.id)  # type: ignore
            .where(and_(BlogTagLink.blog_id == Blog.id, col(Tag.title).in_(tags)))
            .group_by(BlogTagLink.blog_id)  # type: ignore
            .having(func.count(func.distinct(Tag.id)) == len(tags))
        )

        conditions.append(exists(tag_subquery))

    if conditions:
        filtered_query = base_query.where(and_(*conditions))
    else:
        filtered_query = base_query

    # main query with pagination
    blogs_query = (
        filtered_query.where(Blog.is_public)
        .options(selectinload(Blog.tags))  # type: ignore
        .order_by(Blog.id)  # type: ignore
        .limit(limit)
        .offset(offset)
    )

    # create count query
    count_query = (
        select(func.count(Blog.id))  # type: ignore
        .join(BlogLikeLink, Blog.id == BlogLikeLink.blog_id)  # type: ignore
        .where(and_(BlogLikeLink.user_id == user_id, Blog.is_public))
    )

    # apply conditions to count query
    if conditions:
        count_query = count_query.where(and_(*conditions))

    # Execute both queries concurrently
    blogs_result, total_result = await asyncio.gather(
        session.execute(blogs_query), session.execute(count_query)
    )

    blogs = blogs_result.scalars().all()
    total = total_result.scalar_one()

    return blogs, total
