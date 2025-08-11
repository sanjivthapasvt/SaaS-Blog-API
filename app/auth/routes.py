from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.users.models import User
from app.auth.schemas import UserCreate, Token, UserLogin
from app.auth.utils import hash_password, verify_password
from app.auth.auth import create_access_token

router = APIRouter()

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate , session: AsyncSession = Depends(get_session)):
    """
    Register a new user and return an authentication token.

    This endpoint validates the provided username, email, and password,
    creates a new user in the database, and returns a JWT access token.

    Args:
        user_data (UserCreate): The user's registration details.
        session (AsyncSession): The database session dependency.

    Returns:
        Token: A dictionary containing the access token and token type.

    Raises:
        HTTPException:
            - 400: If the username or email already exists.
            - 403: If the password length is less than 6 characters.
            - 500: For unexpected server errors.
    """
    try:
        user = await session.execute(select(User).where(User.username == user_data.username))
        user_result = user.scalars().first()
        email = await session.execute(select(User).where(User.email == user_data.email))
        email_result = email.scalars().first()
        if user_result :
            raise HTTPException(status_code=400, detail="Username already exists")
        if email_result:
            raise HTTPException(status_code=400, detail="Email already exists")

        if(len(user_data.password) < 6):
            raise HTTPException(status_code=403, detail="Password length shoudl be greater than 6")

        full_name = f"{(user_data.first_name).capitalize()} {(user_data.last_name).capitalize()}"
        new_user = User(username=user_data.username,email=user_data.email,full_name=full_name, hashed_password=hash_password(user_data.password))
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        token = create_access_token({"sub":new_user.username})
        
        return {"access_token": token, "token_type": "bearer"}

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, session: AsyncSession = Depends(get_session)):
    """
    Login a existing user and return an authentication token.

    This endpoint validates the provided username and password,
    and returns a JWT access token.

    Args:
        user_data (UserLogin): The user's login details.
        session (AsyncSession): The database session dependency.

    Returns:
        Token: A dictionary containing the access token and token type.

    Raises:
        HTTPException:
            - 400: If the username or password is incorrect.
            - 403: If the password length is less than 6 characters.
            - 500: For unexpected server errors.
    """
    try:
        user = await session.execute(select(User).where(User.username == user_data.username))
        user_result = user.scalars().first()
        if not user_result or not verify_password(user_data.password, user_result.hashed_password): # type: ignore
            raise HTTPException(status_code=400, detail="Incorrect username or password")

        token = create_access_token({"sub": user_result.username})
        
        return {"access_token": token, "token_type": "bearer"}
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
