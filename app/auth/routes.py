from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.dependency import get_user_by_identifier
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt_handler import (
    bearer_scheme,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.auth.schemas import Token, UserCreate, UserLogin
from app.auth.security import TokenBlacklist, get_token_blacklist
from app.core.database import get_session
from app.users.models import User

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(RateLimiter(times=5, minutes=1))],
)
async def login_user_route(
    user_data: UserLogin, session: AsyncSession = Depends(get_session)
):
    """
    Authenticate user and return JWT access token and refresh token.
    """
    try:
        user = await session.execute(
            select(User).where(User.username == user_data.username)
        )
        user_result = user.scalars().first()
        if not user_result or not verify_password(user_data.password, user_result.hashed_password):  # type: ignore
            raise HTTPException(
                status_code=400, detail="Incorrect username or password"
            )

        # create access and refresh tokens
        access_token = create_access_token({"sub": user_result.username})
        refresh_token = create_refresh_token({"sub": user_result.username})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")


@router.post(
    "/register",
    response_model=Token,
    dependencies=[Depends(RateLimiter(times=25, hours=1))],
)
async def register_user_route(
    user_data: UserCreate, session: AsyncSession = Depends(get_session)
):
    """
    Create new user account and return JWT access token and refresh token.
    """
    try:
        # Check if username exists
        user = await session.execute(
            select(User).where(User.username == user_data.username)
        )
        user_result = user.scalars().first()

        # Check if email exists
        email = await session.execute(select(User).where(User.email == user_data.email))
        email_result = email.scalars().first()

        if user_result:
            raise HTTPException(status_code=400, detail="Username already exists")
        if email_result:
            raise HTTPException(status_code=400, detail="Email already exists")

        if len(user_data.password) < 6:
            raise HTTPException(
                status_code=400, detail="Password length should be greater than 6"
            )

        full_name = f"{(user_data.first_name).capitalize()} {(user_data.last_name).capitalize()}"
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=full_name,
            hashed_password=hash_password(user_data.password),
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        # Create access and refresh tokens
        access_token = create_access_token({"sub": new_user.username})
        refresh_token = create_refresh_token({"sub": new_user.username})

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while registering{str(e)}"
        )


@router.post("/logout")
async def logout_user_route(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    blacklist: TokenBlacklist = Depends(get_token_blacklist),
):
    """
    Logout user by blacklisting their current token.
    Requires valid access token in Authorization header.
    """
    try:
        token = credentials.credentials
        payload = decode_token(token, expected_type="access")

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        jti = payload.get("jti")
        exp = payload.get("exp")

        if not jti:
            raise HTTPException(status_code=401, detail="Invalid token structure")

        # Check if token is already blacklisted
        if await blacklist.is_blacklisted(jti):
            raise HTTPException(status_code=401, detail="Token already revoked")

        # Calculate TTL based on token expiration
        if exp:
            current_time = int(datetime.now(timezone.utc).timestamp())
            ttl = exp - current_time

            if ttl > 0:
                await blacklist.blacklist_token(jti, expire=ttl)
            else:
                # Token already expired, but blacklist it anyway
                await blacklist.blacklist_token(jti, expire=60)
        else:
            # No expiration in token, use default TTL
            await blacklist.blacklist_token(jti, expire=3600)

        return {"detail": "Logged out successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/refresh")
async def refresh_token_route(
    refresh_token: str,
    session: AsyncSession = Depends(get_session),
    blacklist: TokenBlacklist = Depends(get_token_blacklist),
):
    """Refresh access token using refresh token"""
    try:
        payload = decode_token(refresh_token, expected_type="refresh")

        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired refresh token",
            )

        # Check if refresh token is blacklisted
        jti = payload.get("jti")
        if jti and await blacklist.is_blacklisted(jti):
            raise HTTPException(
                status_code=401, detail="Refresh token has been revoked"
            )

        sub = payload.get("sub")

        if not sub:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload",
            )

        user = await get_user_by_identifier(session, sub)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found",
            )

        # Blacklist the old refresh token
        if jti:
            exp = payload.get("exp")
            if exp:
                current_time = int(datetime.now(timezone.utc).timestamp())
                ttl = exp - current_time
                if ttl > 0:
                    await blacklist.blacklist_token(jti, expire=ttl)

        # Create new access and refresh tokens
        access_token = create_access_token({"sub": user.username or user.google_id})
        new_refresh_token = create_refresh_token(
            {"sub": user.username or user.google_id}
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,  # Return new refresh token
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
