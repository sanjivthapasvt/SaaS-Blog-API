import json

from app.core.redis import redis_manager
from app.notifications.models import Notification


async def publish_notification(notification: Notification, redis_manager_instance=None):
    """publish notification event to redis"""

    # use provided instance of redis manager or global one
    manager = redis_manager_instance or redis_manager

    # create notification payload
    notification_data = {
        "id": notification.id,
        "type": notification.notification_type,
        "message": notification.message,
        "triggered_by_user_id": notification.triggered_by_user_id,
        "blog_id": notification.blog_id,
        "created_at": notification.created_at.isoformat(),
        "is_read": notification.is_read,
    }

    # publish to redis channel specific to the user
    channel = f"notifications:{notification.owner_id}"
    await manager.publish(channel, json.dumps(notification_data))
