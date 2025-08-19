from sqlmodel import Field, SQLModel
from typing import Optional

class BlogLikeLink(SQLModel, table=True):
    blog_id: Optional[int] = Field(default=None, foreign_key="blog.id", primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", primary_key=True)
