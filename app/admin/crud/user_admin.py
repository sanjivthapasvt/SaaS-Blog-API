import re

from fastapi.exceptions import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.admin.schema import UserCreate, UserUpdate
from app.auth.hashing import hash_password
from app.auth.security import check_password_strength
from app.users.models import User


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


async def list_user_detail(session: AsyncSession, user_id: int):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User doesn't exists!")
    return user


async def create_user(session: AsyncSession, user_data: UserCreate):
    user_data.username = re.sub(r"\s+", "", user_data.username)

    # Check if username exists
    user = await session.execute(
        select(User).where(User.username == user_data.username)
    )
    if user.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    # Check if email exists
    email = await session.execute(select(User).where(User.email == user_data.email))
    if email.scalars().first():
        raise HTTPException(status_code=400, detail="Email already exists")

    strong, reasons = check_password_strength(user_data.password)
    if not strong:
        raise HTTPException(
            status_code=400,
            detail={"password": user_data.password, "reasons": reasons},
        )

    full_name = (
        f"{(user_data.first_name).capitalize()} {(user_data.last_name).capitalize()}"
    )

    hashed_password = hash_password(user_data.password)

    new_user = User(
        username=user_data.username,
        full_name=full_name,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def update_user(session: AsyncSession, user_id: int, user_data: UserUpdate):
    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found!")

    if user_data.username:
        user_data.username = re.sub(r"\s+", "", user_data.username)
        existing_user = await session.execute(
            select(User).where(User.username == user_data.username)
        )
        # Check if username exists
        if existing_user.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Username already exists, please choose another one!",
            )
        user.username = user_data.username

    if user_data.full_name:
        user.full_name = user_data.full_name

    if user_data.password:
        strong, reasons = check_password_strength(user_data.password)
        if not strong:
            raise HTTPException(
                status_code=400,
                detail={"password": user_data.password, "reasons": reasons},
            )
        user.hashed_password = hash_password(user_data.password)

    if user_data.is_active:
        user.is_active = user_data.is_active

    if user_data.is_superuser:
        user.is_superuser = user_data.is_superuser

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user_id: int) -> str | None:
    # Check if user exists
    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User doesn't exist!")

    username = user.username

    await session.delete(user)
    await session.commit()
    return username
