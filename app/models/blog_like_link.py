from sqlmodel import SQLModel, Field

class BlogLikeLink(SQLModel, table=True):
    blog_id: int | None = Field(default=None, foreign_key="blog.id", primary_key=True)
    user_id: int | None = Field(default=None, foreign_key='user.id', primary_key=True)
    