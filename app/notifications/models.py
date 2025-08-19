from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlmodel import Column, Field, SQLModel, Text


class NotificationType(str, Enum):
    GENERAL = ("general",)
    LIKE = ("like",)
    NEW_BLOG = ("new_blog",)
    FOLLOW = ("follow",)
    COMMENT = "comment"


class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id", index=True)
    blog_id: Optional[int] = Field(default=None, foreign_key="blog.id", index=True)
    triggered_by_user_id: int = Field(foreign_key="user.id", index=True)
    notification_type: NotificationType = Field(
        default=NotificationType.GENERAL, index=True
    )
    message: str = Field(sa_column=Column(Text))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    is_read: bool = False
