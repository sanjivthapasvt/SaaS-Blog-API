from pydantic import BaseModel

class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    message: str