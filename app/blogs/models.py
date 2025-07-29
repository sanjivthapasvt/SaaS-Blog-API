from sqlmodel import SQLModel, Field
from datetime import timezone, datetime


class Blog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    thumbnail_url: str | None = Field(default=None)
    content: str
    uploaded_by: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Comments(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    blog_id: int | None = Field(default=None, foreign_key="blog.id")
    content: str
    commmented_by: str | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
