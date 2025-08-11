import os
import httpx
from urllib.parse import urlencode
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import select
from app.users.models import User
from app.core.database import get_session
from app.auth.auth import create_access_token

router = APIRouter()

#get google client id, secret, and uri from env variable
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


#this get method redirects you to google login page
@router.get("/google")
async def get_google_login_url():
    """
    Redirects user to  google login .

    This endpoint creates new url for google login using GOOGLE_SECRET_ID and
    GOOGLE_CLIENT_SECRET and redirects user to that page

    Args:

    Returns:
        REdirect: To google login page
    Raises:
        HTTPException:
            - 500: For unexpected server errors.
    """
    scopes = [
        "openid",
        "email",
        "profile",
    ]

    params = {
        "response_type": "code",
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "scope": " ".join(scopes),
        "access_type": "offline",
        "prompt": "consent"
    }
    
    url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)

    return RedirectResponse(url=url, status_code=302)


# The google redirect uri should be same as path here 
# In my case In google I have set GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
# The google returns access_token and we can use it to get user info including id, email, name and picture
@router.get("/google/callback")
async def auth_google(code: str, session: AsyncSession = Depends(get_session)):
    """
    Register or Login user after user completes google login

    This endpoint is called by google with their code and google 
    sends access_token as response and we use that token to get user
    info including google_id, email and name and validates if the user
    already has account or not and creates if not and return access token in both cases

    Args:
        code (str): Google returns code after user successfully logs in on google auth.
        session (AsyncSession): The database session dependency.

    Returns:
        Token: A dictionary containing the access token and token type.

    Raises:
        HTTPException:
            - 400: If google send incoplete info.
            - 500: For unexpected server errors.
    """
    try:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        response = httpx.post(token_url, data=data)
        response.raise_for_status()

        data = response.json()
        access_token = data["access_token"]
        
        user_info_resp = httpx.get(
            "https://www.googleapis.com/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"})
        user_info_resp.raise_for_status()
        user_info = user_info_resp.json()
        id = user_info["id"]
        name = user_info["name"]
        email = user_info["email"]
        picture = user_info["picture"]
        if not name or not email or not id:
            raise HTTPException(status_code=400, detail="Incomplete user info from Google")
        
        user = await check_user_exist(google_id=id, session=session)

        if not user:
            existing_user_result = await session.execute(select(User).where(email == User.email))
            existing_user = existing_user_result.scalars().first()
            if existing_user and not existing_user.google_id:
                existing_user.google_id = id
                await session.commit()
                await session.refresh(existing_user)
                user = existing_user

            user = await create_new_user(google_id=user_info["id"], name=user_info["name"], email=user_info["email"], profile_pic=picture, session=session)

        token = create_access_token({"sub": user.google_id})

        return {"access_token": token, "token_type": "bearer"}
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while authenticating {str(e)}")



async def check_user_exist(google_id: str, session: AsyncSession) -> User | None:
    """
    Dependency for auth_google to check if user already exist in database or not

    Args:
        google_id (str): The user's google_id.
        session (AsyncSession): The database session dependency.

    Returns:
        User: If the user already exists  in database
        None: If the user doesn't exist in database

    """
    user = await session.execute(select(User).where(User.google_id == google_id))
    return user.scalars().first()


async def create_new_user(google_id: str, name: str, email: str, profile_pic: str | None, session: AsyncSession) -> User:
    """
    Creates new user in database.

    Args:
        google_id (str): The user google_id.
        name (str): The user full name
        email(str): The user mail
        profile_pic: The user google picture
        session (AsyncSession): The database session dependency.

    Returns:
        User: Creates new user and return it
    Raises:
        HTTPException:
            - 500: For unexpected server errors.
    """
    try:
        user = User(username=None, google_id=google_id ,email=email, full_name=name, profile_pic=profile_pic, is_active=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while creating user {str(e)}")