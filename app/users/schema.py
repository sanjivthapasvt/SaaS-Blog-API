from datetime import datetime
from pydantic import BaseModel

class UserRead(BaseModel):
    id: int
    full_name: str
    profile_pic: str | None

class CurrentUserRead(BaseModel):
    id: int
    username: str | None
    full_name: str | None
    profile_pic: str | None
    email: str | None
    joined_at: datetime

class UserChangePassword(BaseModel):
    current_password: str
    new_password: str
    again_new_password: str