from fastapi.exceptions import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.notifications.models import Notification


async def get_notifications(
    search: str | None,
    limit: int,
    offset: int,
    session: AsyncSession,
    current_user: int,
):
    query = (
        select(Notification)
        .where(Notification.owner_id == current_user)
        .limit(limit)
        .offset(offset)
    )
    total_query = (
        select(func.count())
        .select_from(Notification)
        .where(Notification.owner_id == current_user)
    )

    if search:
        search_term = f"%{search.lower()}%"
        condition = func.lower(Notification.message).like(search_term)
        query = query.where(condition)
        total_query = total_query.where(condition)

    notifications = await session.execute(query)
    notifications_result = notifications.scalars().all()
    total = await session.execute(total_query)
    total_result = total.scalars().one()

    return notifications_result, total_result


async def mark_notification_as_read(
    session: AsyncSession, notification_id: int, current_user: int
):
    notification = await session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail=f"Notificaiton not found")

    if not notification.owner_id == current_user:
        raise HTTPException(
            status_code=403, detail="You are not the owner of the notification"
        )

    if notification.is_read:
        return {"detail": "Already makred as read"}
    notification.is_read = True
    session.add(notification)
    await session.commit()
    await session.refresh(notification)
    return {"detail": "Marked notification as read"}
