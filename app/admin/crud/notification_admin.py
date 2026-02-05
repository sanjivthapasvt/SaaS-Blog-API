from fastapi.exceptions import HTTPException
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.admin.schema import NotificationCreate
from app.notifications.models import Notification


async def list_notifications(
    search: str | None, limit: int, offset: int, session: AsyncSession
):
    query = select(Notification)
    total_query = select(func.count()).select_from(Notification)

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Notification.message).like(search_term)
        query = query.where(condition)

    query = query.order_by(Notification.created_at.desc())

    total = await session.execute(total_query)
    total_result = total.scalars().one()

    notifications = await session.execute(query.limit(limit).offset(offset))
    notifications_result = notifications.scalars().all()

    return {
        "total": total_result,
        "limit": limit,
        "offset": offset,
        "data": notifications_result,
    }


async def get_notification(session: AsyncSession, notification_id: int):
    notification = await session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found!")
    return notification


async def create_notification(session: AsyncSession, notification_data: NotificationCreate):
    new_notification = Notification(
        owner_id=notification_data.owner_id,
        blog_id=notification_data.blog_id,
        triggered_by_user_id=notification_data.triggered_by_user_id,
        notification_type=notification_data.notification_type,
        message=notification_data.message,
    )
    session.add(new_notification)
    await session.commit()
    await session.refresh(new_notification)
    return new_notification


async def delete_notification(session: AsyncSession, notification_id: int) -> str:
    notification = await session.get(Notification, notification_id)
    if not notification:
         raise HTTPException(status_code=404, detail="Notification not found!")
    
    await session.delete(notification)
    await session.commit()
    return "Notification deleted"
