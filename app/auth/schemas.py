from typing import Annotated
from pydantic import EmailStr, constr, BaseModel
from sqlmodel import SQLModel


class UserCreate(SQLModel):
    username: Annotated[str, constr(min_length=3, max_length=50)]
    first_name: Annotated[str, constr(min_length=3, max_length=20)]
    last_name: Annotated[str, constr(min_length=3, max_length=25)]
    email: EmailStr
    password: Annotated[str, constr(min_length=6, max_length=250)]


class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: int
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str
