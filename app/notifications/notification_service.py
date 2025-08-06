from sqlmodel import Session
from notifications.models import NotificationType, Notification
from utils.logger import logger

def create_notfication(
    user_id: int,
    message: str,
    notification_type: NotificationType,
    session: Session,
):
    try:
        notification = Notification(user_id=user_id, notification_type=notification_type, message=message)
        session.add(notification)
        session.commit()
        session.refresh(notification)
    
    except Exception as e:
        logger.error(f"Something went wrong while creating notification {str(e)}")