from fastapi import APIRouter, Depends, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from app.admin.crud.user_admin import create_user
from app.admin.schema import UserCreate
from app.admin.utils import get_is_admin_user
from app.core.services.database import get_session

router = APIRouter(tags=["Admin - User"])

@router.post(
    "/user",
    dependencies=[Depends(RateLimiter(times=15, hours=1)), Depends(get_is_admin_user)],
)
async def register_user_route(
    user_data: UserCreate, session: AsyncSession = Depends(get_session),
):
    """
    Create new user by admin
    """
    try:
        user =  await create_user(session, user_data)
        return f"Created user {user.username} successfully!"
    except HTTPException:
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Something went wrong while registering{str(e)}"
        )
