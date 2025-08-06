from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select
from auth.auth import get_current_user
from core.database import get_session
from users.models import User
from notifications.models import Notification
from notifications.schema import NotificationResponse
from models.schema import PaginatedResponse
router = APIRouter()

@router.get("/notification", response_model=PaginatedResponse[NotificationResponse])
async def get_notifications(
    search: str | None = Query(default=None),
    limit: int = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),    
):
    try:
        query = select(Notification).limit(limit).offset(offset).where(Notification.user_id == current_user.id)
        total_query = select(func.count()).select_from(Notification).where(Notification.user_id == current_user.id)
        
        if search:
            search_term = f"%{search.lower()}%"
            condition = func.lower(Notification.message).like(search_term)
            query = query.where(condition)
            total_query = total_query.where(condition)
        
        notifications = session.exec(query).all()
        total = session.exec(total_query).one()

        result = [{
            "id":  notification.id,
            "notification_type": notification.notification_type,
            "message": notification.message,
        }for notification in notifications]

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": result,
        }
    
    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Something went wrong while getting notification {str(e)}")