from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud import (authenticate_user, logout_user, refresh_tokens,
                           register_user)
from app.auth.jwt_handler import bearer_scheme
from app.auth.schemas import Token, UserCreate, UserLogin
from app.auth.security import TokenBlacklist, get_token_blacklist
from app.core.database import get_session

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
        return await authenticate_user(session, user_data.username, user_data.password)
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
        return await register_user(session, user_data)

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
        return await logout_user(credentials.credentials, blacklist)
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
        return await refresh_tokens(session, refresh_token, blacklist)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
