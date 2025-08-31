import re
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.dependency import get_user_by_identifier
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import (create_access_token, create_refresh_token,
                                  decode_token)
from app.auth.security import TokenBlacklist, check_password_strength
from app.users.models import User


##############################
# ---------- LOGIN ----------#
##############################
async def authenticate_user(session: AsyncSession, username: str, password: str):
    user = await session.execute(select(User).where(User.username == username))
    user_result = user.scalars().first()

    if not user_result or not verify_password(password, user_result.hashed_password):  # type: ignore
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token = create_access_token({"sub": user_result.username})
    refresh_token = create_refresh_token({"sub": user_result.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


##############################
# --------- Register---------#
##############################


async def register_user(session: AsyncSession, user_data):
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
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=full_name,
        hashed_password=hash_password(user_data.password),
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    access_token = create_access_token({"sub": new_user.username})
    refresh_token = create_refresh_token({"sub": new_user.username})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


##############################
# ----------LOGOUT -----------#
##############################


async def logout_user(token: str, blacklist: TokenBlacklist):
    payload = decode_token(token, expected_type="access")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    jti = payload.get("jti")
    exp = payload.get("exp")

    if not jti:
        raise HTTPException(status_code=401, detail="Invalid token structure")

    if await blacklist.is_blacklisted(jti):
        raise HTTPException(status_code=401, detail="Token already revoked")

    # Calculate TTL
    if exp:
        current_time = int(datetime.now(timezone.utc).timestamp())
        ttl = exp - current_time
        await blacklist.blacklist_token(jti, expire=ttl if ttl > 0 else 60)
    else:
        await blacklist.blacklist_token(jti, expire=3600)

    return {"detail": "Logged out successfully"}


##############################
# ----------REFRESH----------#
##############################
async def refresh_tokens(
    session: AsyncSession, refresh_token: str, blacklist: TokenBlacklist
):
    payload = decode_token(refresh_token, expected_type="refresh")

    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    jti = payload.get("jti")
    if jti and await blacklist.is_blacklisted(jti):
        raise HTTPException(status_code=401, detail="Refresh token has been revoked")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await get_user_by_identifier(session, sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Blacklist old refresh token
    if jti:
        exp = payload.get("exp")
        if exp:
            current_time = int(datetime.now(timezone.utc).timestamp())
            ttl = exp - current_time
            if ttl > 0:
                await blacklist.blacklist_token(jti, expire=ttl)

    access_token = create_access_token({"sub": user.username or user.google_id})
    new_refresh_token = create_refresh_token({"sub": user.username or user.google_id})

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }
