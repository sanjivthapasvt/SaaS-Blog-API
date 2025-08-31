import asyncio

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.blogs.models import Blog
from app.users.models import BookMark, User, UserFollowLink

profile_pic_path: str = "users/profile_pic"


async def list_user_info(session: AsyncSession, user_id: int):
    query = select(User).where(User.id == user_id)
    user_data = await session.execute(query)
    user_data_result = user_data.scalars().first()

    return user_data_result


async def list_user_bookmarks(
    user_id: int, search: str | None, limit: int, offset: int, session: AsyncSession
):
    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    blogs_query = (
        select(Blog)
        .options(selectinload(Blog.tags))  # type: ignore
        .join(BookMark, Blog.id == BookMark.blog_id)  # type: ignore
        .where(BookMark.user_id == user_id)
    )
    condition = None

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Blog.title).like(search_term)
        blogs_query = blogs_query.where(condition)

    total_query = (
        select(func.count())
        .select_from(Blog)
        .join(BookMark, Blog.id == BookMark.blog_id)  # type: ignore
        .where(BookMark.user_id == user_id)
    )

    if condition is not None:
        total_query = total_query.where(condition)

    blogs_result, total_result = await asyncio.gather(
        session.execute(blogs_query.limit(limit).offset(offset)),
        session.execute(total_query),
    )

    blogs = blogs_result.scalars().all()
    total = total_result.scalar_one()

    return blogs, total


async def list_users(
    search: str | None, limit: int, offset: int, session: AsyncSession
):
    query = select(User)
    total_query = select(func.count()).select_from(User)

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(User.full_name).like(search_term)
        query = query.where(condition)

    total = await session.execute(total_query.limit(limit).offset(offset))
    total_result = total.scalars().one()
    users = await session.execute(query)
    users_result = users.scalars().all()

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": users_result,
    }


async def list_followers(
    user_id: int, search: str | None, limit: int, offset: int, session: AsyncSession
):
    if not await session.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    base_query = (
        select(User)
        .join(UserFollowLink, User.id == UserFollowLink.follower_id)  # type: ignore
        .where(UserFollowLink.following_id == user_id)
    )

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(User.full_name).like(search_term)
        base_query = base_query.where(condition)

    total_query = select(func.count()).select_from(base_query.subquery())
    total_result = await session.execute(total_query)
    total_count = total_result.scalar() or 0

    followers_query = base_query.limit(limit).offset(offset).order_by(User.full_name)

    followers_result = await session.execute(followers_query)
    followers = followers_result.scalars().all()

    return followers, total_count


async def list_followings(
    user_id: int, search: str | None, limit: int, offset: int, session: AsyncSession
):
    if not await session.get(User, user_id):
        raise HTTPException(status_code=404, detail="User not found")

    base_query = (
        select(User)
        .join(UserFollowLink, User.id == UserFollowLink.following_id)  # type: ignore
        .where(UserFollowLink.follower_id == user_id)
    )

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(User.full_name).like(search_term)
        base_query = base_query.where(condition)

    total_query = select(func.count()).select_from(base_query.subquery())
    total_result = await session.execute(total_query)
    total_count = total_result.scalar() or 0

    followings_query = base_query.limit(limit).offset(offset).order_by(User.full_name)

    followings_result = await session.execute(followings_query)
    followings = followings_result.scalars().all()

    return followings, total_count
