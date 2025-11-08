import re
from app.admin.schema import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete
from fastapi.exceptions import HTTPException
from app.auth.hashing import hash_password
from app.auth.security import check_password_strength
from app.users.models import User


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
    
    new_user = User(username=user_data.username, full_name=full_name, email=user_data.email, hashed_password=hashed_password)
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return new_user


async def delete_user(session: AsyncSession, user_id: int) -> str | None:
    # Check if user exists
    user = await session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User doesn't exist!")
    
    username = user.username
    
    await session.delete(user)
    await session.commit()
    return username