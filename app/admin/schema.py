from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints


class UserCreate(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    first_name: Annotated[str, StringConstraints(min_length=3, max_length=20)]
    last_name: Annotated[str, StringConstraints(min_length=3, max_length=25)]
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=250)]


class UserUpdate(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)] | None
    full_name: Annotated[str, StringConstraints(min_length=5, max_length=100)] | None
    password: Annotated[str, StringConstraints(min_length=8, max_length=250)] | None
    is_active: bool | None
    is_superuser: bool | None


class UserDetail(BaseModel):
    username: str | None
    full_name: str | None
    profile_pic: str | None
    email: str | None
    bio: str | None
    joined_at: datetime
    is_active: bool
    is_superuser: bool
