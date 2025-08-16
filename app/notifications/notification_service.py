from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification, NotificationType
from app.utils.logger import logger


async def create_notfication(
    owner_id: int,
    triggered_by_user_id: int,
    message: str,
    notification_type: NotificationType,
    blog_id: int | None,
    session: AsyncSession,
):
    try:
        notification = Notification(
            owner_id=owner_id,
            triggered_by_user_id=triggered_by_user_id,
            notification_type=notification_type,
            blog_id=blog_id,
            message=message,
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)

    except Exception as e:
        logger.error(f"Something went wrong while creating notification {str(e)}")
