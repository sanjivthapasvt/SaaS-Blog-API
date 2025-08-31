from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.auth.google_crud import generate_google_login_url, authenticate_with_google

router = APIRouter()


@router.get("/google", dependencies=[Depends(RateLimiter(times=5, minutes=15))])
async def get_google_login_url():
    """
    Redirect user to Google OAuth login page
    """
    url = generate_google_login_url()
    return RedirectResponse(url=url, status_code=302)


@router.get("/google/callback", dependencies=[Depends(RateLimiter(times=5, minutes=15))])
async def auth_google(code: str, session: AsyncSession = Depends(get_session)):
    """
    Handle Google callback, login/register user, return JWTs
    """
    return await authenticate_with_google(code, session)
