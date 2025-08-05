import os
from urllib.parse import urlencode
import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from users.models import User
from core.database import get_session
from auth.auth import create_access_token

router = APIRouter()

#get google client id, secret, and uri from env variable
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")


#this get method redirects you to google login page
@router.get("/google")
async def get_google_login_url():
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
async def auth_google(code: str, session: Session = Depends(get_session)):
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
        
        user = check_user_exist(user_id=id, session=session)

        if not user:
            existing_user = session.exec(select(User).where(email == User.email)).first()
            if existing_user and not existing_user.google_id:
                existing_user.google_id = id
                session.commit()
                session.refresh(existing_user)
                user = existing_user

            user = create_new_user(user_id=user_info["id"], name=user_info["name"], email=user_info["email"], profile_pic=picture, session=session)

        token = create_access_token({"sub": user.google_id})

        return {"access_token": token, "token_type": "bearer"}
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while authenticating {str(e)}")


def check_user_exist(user_id: str, session: Session):
    return session.exec(select(User).where(User.google_id == user_id)).first()


def create_new_user(user_id: str, name: str, email: str, profile_pic: str, session: Session):
    try:
        user = User(username=None, google_id=user_id ,email=email, full_name=name, profile_pic=profile_pic, is_active=True)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while creating user {str(e)}")