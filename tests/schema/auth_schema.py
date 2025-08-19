from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints


class UserCreate(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    first_name: Annotated[str, StringConstraints(min_length=3, max_length=20)]
    last_name: Annotated[str, StringConstraints(min_length=3, max_length=25)]
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=250)]

class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
