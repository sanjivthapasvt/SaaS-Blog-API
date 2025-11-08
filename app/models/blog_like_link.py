from typing import Optional

from sqlmodel import Field, SQLModel


class BlogLikeLink(SQLModel, table=True):
    blog_id: Optional[int] = Field(
        default=None, foreign_key="blog.id", primary_key=True, ondelete="CASCADE"
    )
    user_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
