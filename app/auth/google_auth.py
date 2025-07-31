import os
from urllib.parse import urlencode
import requests
from fastapi import APIRouter
from fastapi.responses import RedirectResponse

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

    return RedirectResponse(url=url, status_code=301)


# The google redirect uri should be same as path here 
# In my case In google I have set GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
# The google returns user info including id, email, name and picture
@router.get("/google/callback")
async def auth_google(code: str):
    token_url = "https://accounts.google.com/o/oauth2/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }
    response = requests.post(token_url, data=data)
    data = response.json()
    access_token = data["access_token"]
    access_token_expires_in = data["expires_in"]
    refresh_token = data["refresh_token"]

    
    user_info_resp = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo",
        headers={"Authorization": f"Bearer {access_token}"})
    user_info = user_info_resp.json()
    
    user_data = {
        "name": user_info["name"],
        "email": user_info["email"],
        "picture": user_info["picture"],
    }

    #return user info like id, name, email and also access and refresh tokens
    return {
        "user": user_data,
        "token": {
            "access_token": access_token,
            "access_token_expires_in": access_token_expires_in,
            "refresh_token": refresh_token,
        }
    }
