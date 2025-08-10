from sqlalchemy.ext.asyncio import AsyncSession
from app.notifications.models import NotificationType, Notification
from app.utils.logger import logger

async def create_notfication(
    user_id: int,
    message: str,
    notification_type: NotificationType,
    session: AsyncSession,
):
    try:
        notification = Notification(user_id=user_id, notification_type=notification_type, message=message)
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
    
    except Exception as e:
        logger.error(f"Something went wrong while creating notification {str(e)}")