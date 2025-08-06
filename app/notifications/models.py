from blogs.models import Blog
from users.models import User
from sqlmodel import SQLModel, Field
from enum import Enum

class NotificationType(str, Enum):
    GENERAL = "general",
    LIKE = "like",
    FOLLOW = "follow",
    COMMENT = "comment"

class Notification(SQLModel, table=True):
    id:int | None = Field(default=None, primary_key=True)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    notification_type: NotificationType = Field(default=NotificationType.GENERAL, index=True)
    message: str = Field()
    is_read: bool = False