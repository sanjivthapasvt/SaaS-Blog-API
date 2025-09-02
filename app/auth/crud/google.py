import os
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.jwt_handler import create_access_token, create_refresh_token
from app.users.models import User

# Load env vars
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL")


##################################################
# ----------- Generate Google Login URL ----------#
##################################################
def generate_google_login_url() -> str:
    scopes = ["openid", "email", "profile"]

    params = {
        "response_type": "code",
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent",
    }

    return "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)


###############################################
# ----------- Handle Google Callback ----------#
###############################################
async def authenticate_with_google(code: str, session: AsyncSession):
    """
    Exchange code for token, fetch user info, register/login user, return JWTs
    """
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_resp.raise_for_status()
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(
                status_code=400, detail="Failed to retrieve access token"
            )

        # Get user info
        user_info_resp = await client.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        user_info_resp.raise_for_status()
        user_info = user_info_resp.json()

    google_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")

    if not google_id or not email or not name:
        raise HTTPException(status_code=400, detail="Incomplete user info from Google")

    # Check if user exists
    user_result = await session.execute(select(User).where(User.google_id == google_id))
    user = user_result.scalars().first()

    if not user:
        # Check if a user exists with the same email
        existing_user_result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = existing_user_result.scalars().first()

        if existing_user and not existing_user.google_id:
            existing_user.google_id = google_id
            await session.commit()
            await session.refresh(existing_user)
            user = existing_user
        else:
            # Create new user
            user = User(
                username=None,
                google_id=google_id,
                email=email,
                full_name=name,
                profile_pic=picture,
                is_active=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

    # Create JWT tokens
    jwt_access_token = create_access_token({"sub": user.google_id})
    jwt_refresh_token = create_refresh_token({"sub": user.google_id})

    return {
        "access_token": jwt_access_token,
        "refresh_token": jwt_refresh_token,
        "token_type": "bearer",
    }

    # Redirect user to frontend with tokens
    # redirect_url = f"{FRONTEND_URL}/auth/success?access={jwt_access_token}&refresh={jwt_refresh_token}"
    # return RedirectResponse(url=redirect_url)


############################################
# ----------- Check Existing User ----------#
############################################
async def check_user_exist(google_id: str, session: AsyncSession) -> User | None:
    user = await session.execute(select(User).where(User.google_id == google_id))
    return user.scalars().first()


########################################
##---------- Create New User ----------#
########################################
async def create_new_user(
    google_id: str,
    name: str,
    email: str,
    profile_pic: str | None,
    session: AsyncSession,
) -> User:
    try:
        user = User(
            username=None,
            google_id=google_id,
            email=email,
            full_name=name,
            profile_pic=profile_pic,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while creating user {str(e)}"
        )
