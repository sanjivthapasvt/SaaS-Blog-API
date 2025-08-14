from sqlmodel import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.notifications.models import Notification
from fastapi.exceptions import HTTPException

async def get_notifications(search: str | None, limit: int , offset: int, session: AsyncSession, current_user: int):
    query = select(Notification).where(Notification.owner == current_user).limit(limit).offset(offset)
    total_query = select(func.count()).select_from(Notification).where(Notification.owner == current_user)
        
    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Notification.message).like(search_term)
        query = query.where(condition)
        total_query = total_query.where(condition)
        
    notifications = await session.execute(query)
    notifications_result = notifications.scalars().all()
    total = await session.execute(total_query)
    total_result = total.scalars().one()

    result = [{
        "id":  notification.id,
        "notification_type": notification.notification_type,
        "message": notification.message,
        "blog_id": notification.blog_id,
        "created_at": notification.created_at,
    }for notification in notifications_result]

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": result,
    }


async def mark_notification_as_read(session: AsyncSession, notification_id: int, current_user: int):
    notification = await session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail=f"Notificaiton not found")

    if not notification.owner == current_user:
        raise HTTPException(status_code=401, detail="You are not the owner of the notification")

    notification.is_read = True
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return {"detail": "Makred notification as read"}