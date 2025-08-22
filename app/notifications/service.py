from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification, NotificationType
from app.realtime.events import publish_notification
from app.utils.logger import logger


async def create_notification(
    owner_id: int,
    triggered_by_user_id: int,
    message: str,
    notification_type: NotificationType,
    blog_id: int | None,
    session: AsyncSession,
    request: Request | None = None,
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

        # Publish real-time event if request is available
        if request and hasattr(request.app.state, "redis_manager"):
            try:
                await publish_notification(
                    notification, request.app.state.redis_manager
                )
            except Exception as e:
                logger.error(f"Failed to publish notification {notification.id}: {e}")
        else:
            logger.warning(
                "Redis manager not available, notification not published to real-time"
            )

    except Exception as e:
        logger.error(f"Something went wrong while creating notification {str(e)}")
