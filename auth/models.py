from sqlmodel import SQLModel, Field
from datetime import datetime
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True,)
    email: str = Field(unique=True, index=True)
    full_name: str = Field(default=None)
    joined_at: str | None= Field(default=datetime.now())
    hashed_password: str