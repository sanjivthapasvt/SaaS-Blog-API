from pydantic import BaseModel
from datetime import datetime
class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    message: str
    created_at: datetime
    blog_id: int | None