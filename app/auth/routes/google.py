from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.crud.google import (authenticate_with_google,
                                  generate_google_login_url)
from app.core.services.database import get_session

router = APIRouter(tags=["Auth - Google"])


@router.get("/google", dependencies=[Depends(RateLimiter(times=5, minutes=15))])
async def get_google_login_url():
    """
    Redirect user to Google OAuth login page
    """
    try:
        url = generate_google_login_url()
        return RedirectResponse(url=url, status_code=302)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error authenticating with Google: {str(e)}"
        )


@router.get(
    "/google/callback", dependencies=[Depends(RateLimiter(times=5, minutes=15))]
)
async def auth_google(code: str, session: AsyncSession = Depends(get_session)):
    """
    Handle Google callback, login/register user, return JWTs
    """
    try:
        return await authenticate_with_google(code, session)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error authenticating with Google: {str(e)}"
        )
