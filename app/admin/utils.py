from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependency import get_user_by_identifier
from app.auth.jwt_handler import bearer_scheme, decode_token
from app.auth.security import get_token_blacklist
from app.core.services.database import get_session



async def get_is_admin_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
):
    """
    Get current authenticated user from JWT token.
    Validates token and checks blacklist.
    """
    token = credentials.credentials
    payload = decode_token(token, expected_type="access")

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if token is blacklisted
    jti = payload.get("jti")
    if jti:
        blacklist = await get_token_blacklist(request)
        if await blacklist.is_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_user_by_identifier(session, sub)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have permisssion for this action",
        )
        
    return user