import asyncio

from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.auth.hashing import hash_password, verify_password
from app.auth.security import check_password_strength
from app.blogs.models import Blog
from app.users.models import BookMark, User
from app.utils.remove_image import remove_image
from app.utils.save_image import save_image

profile_pic_path: str = "users/profile_pic"


async def change_user_password(
    session: AsyncSession,
    current_user: User,
    current_password: str,
    new_password: str,
    again_new_password: str,
):
    if current_user.hashed_password:
        if not verify_password(current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=400, detail="Your old password doesn't match"
            )

    strong, reasons = check_password_strength(new_password)
    if not strong:
        raise HTTPException(
            status_code=400, detail={"password": new_password, "reasons": reasons}
        )

    if new_password != again_new_password:
        raise HTTPException(status_code=400, detail="New passwords doesn't match")

    hashed_new_password = hash_password(new_password)

    current_user.hashed_password = hashed_new_password
    session.add(current_user)
    await session.commit()


async def update_user_profile(
    full_name: str | None,
    profile_pic: UploadFile | None,
    session: AsyncSession,
    current_user: User,
):
    if not full_name and not profile_pic:
        raise HTTPException(
            status_code=400,
            detail="Both fields cannot be empty. At least one field must be provided",
        )

    if full_name is not None and full_name.strip() != "":
        current_user.full_name = full_name

    if profile_pic:
        if current_user.profile_pic:
            await remove_image(current_user.profile_pic)
        profile_pic_url = await save_image(profile_pic, profile_pic_path)
        current_user.profile_pic = profile_pic_url

    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)


async def get_user_bookmarks(
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
        session.execute(blogs_query), session.execute(total_query)
    )

    blogs = blogs_result.scalars().all()
    total = total_result.scalar_one()

    return blogs, total
