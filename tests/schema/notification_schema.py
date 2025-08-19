from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    message: str
    triggered_by_user_id: int
    created_at: datetime
    blog_id: int | None

    model_config = ConfigDict(from_attributes=True)
