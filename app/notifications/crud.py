from sqlmodel import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.notifications.models import Notification


async def get_notifications(search: str | None, limit: int , offset: int, session: AsyncSession, current_user: int):
    query = select(Notification).where(Notification.user_id == current_user).limit(limit).offset(offset)
    total_query = select(func.count()).select_from(Notification).where(Notification.user_id == current_user)
        
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