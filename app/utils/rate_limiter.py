from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.jwt_handler import decode_token
from app.core.database import get_session
from app.users.models import User


async def get_user_for_rate_limit(
    request: Request, session: AsyncSession = Depends(get_session)
):
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        sub = decode_token(token, expected_type="access")

        if not sub:
            return None

        user = await session.execute(select(User).where(User.username == sub))
        user_result = user.scalars().first()

        if not user_result:
            user = await session.execute(select(User).where(User.google_id == sub))
            user_result = user.scalars().first()

        return user_result
    except Exception:
        return None


async def user_identifier(
    request: Request, session: AsyncSession = Depends(get_session)
):
    user = await get_user_for_rate_limit(request, session)
    if user:
        return f"user:{user.id}"
    else:  # fallbak to ip identifier if user is not logged in
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0]}"
        return f"ip:{request.client.host}"  # type: ignore
