from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from core.database import get_session
from users.models import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), session: Session = Depends(get_session)):
    try:
        token = credentials.credentials
        sub = decode_access_token(token)
        
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing sub")
        
        user = session.exec(select(User).where(User.username == sub)).first()

        if not user:
            user = session.exec(select(User).where(User.google_id == sub)).first()
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
        return user
    
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")