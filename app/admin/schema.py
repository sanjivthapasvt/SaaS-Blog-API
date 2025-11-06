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
    first_name: Annotated[str, StringConstraints(min_length=3, max_length=20)] | None
    last_name: Annotated[str, StringConstraints(min_length=3, max_length=25)] | None
    email: EmailStr | None
    password: Annotated[str, StringConstraints(min_length=8, max_length=250)] | None
    profile_pic: str | None
    bio: str | None
    is_active: bool | None
    is_superuser: bool | None