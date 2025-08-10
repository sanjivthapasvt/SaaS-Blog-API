from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.core.database import get_session
from app.users.models import User
import os

SECRET_KEY = os.getenv("SECRET_KEY") or "sanjivthapafastapisecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

bearer_scheme = HTTPBearer()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    
    except JWTError:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), session: AsyncSession = Depends(get_session)):
    try:
        token = credentials.credentials
        sub = decode_access_token(token)
        
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token or Token has been expired")
        
        user = await session.execute(select(User).where(User.username == sub))
        user_result = user.scalars().first()

        if not user_result:
            user = await session.execute(select(User).where(User.google_id == sub))
            user_result = user.scalars().first()
        
        if not user_result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return user_result
    
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")