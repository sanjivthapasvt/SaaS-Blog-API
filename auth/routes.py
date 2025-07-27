from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from core.database import get_session
from auth.models import User
from auth.schemas import UserCreate, Token, UserRead
from auth.utils import hash_password, verify_password
from auth.auth import create_access_token, get_current_user
router = APIRouter()

@router.post("/register", response_model=Token)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == user_data.username)).first()
    email = session.exec(select(User).where(User.email == user_data.email)).first()

    if user:
        raise HTTPException(status_code=400, detail="Username already exists")
    if email:
        raise HTTPException(status_code=400, detail="Email already exists")

    def validate_password(password: str):
        if(len(password) < 6):
            raise HTTPException(status_code=403, detail="Password length shoudl be greater than 6")
    validate_password(user_data.password)

    full_name = f"{(user_data.first_name).capitalize()} {(user_data.last_name).capitalize()}"
    new_user = User(username=user_data.username,email=user_data.email,full_name=full_name, hashed_password=hash_password(user_data.password))
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    user = (session.exec(select(User).where(User.username == user_data.username)).first())
    token = create_access_token({"sub":user.username}) # type: ignore
    
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    token = create_access_token({"sub": user.username})
    
    return {"access_token": token, "token_type": "bearer"}

@router.get("/users/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
