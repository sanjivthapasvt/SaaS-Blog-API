from sqlmodel import SQLModel, Field
from datetime import datetime
class Blog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    thumbnail: str | None = Field(default=None)
    content: str
    uploaded_by: int | None = Field(default=None, foreign_key="user.id")
    created_at: str = Field(default=datetime.now())

class Comments(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    blog_id: int | None = Field(default=None, foreign_key="blog.id")
    content: str
    commmented_by: str | None = Field(default=None, foreign_key="user.id")
    created_at: str | None = Field(default=datetime.now())