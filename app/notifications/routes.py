from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.auth import get_current_user
from app.core.database import get_session
from app.users.models import User
from app.notifications.schema import NotificationResponse
from app.models.schema import PaginatedResponse
from app.notifications.crud import get_notifications


router = APIRouter()

@router.get("/notifications", response_model=PaginatedResponse[NotificationResponse])
async def get_notifications_route(
    search: str | None = Query(default=None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),    
):
    try:
        return await get_notifications(session=session, search=search, limit=limit, offset=offset, current_user=current_user.id) # type: ignore
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while getting notification {str(e)}")