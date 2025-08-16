from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlmodel import Column, Field, Relationship, SQLModel, Text

from app.models.blog_like_link import BlogLikeLink

if TYPE_CHECKING:
    from users.models import User


class BlogTagLink(SQLModel, table=True):
    blog_id: int | None = Field(default=None, foreign_key="blog.id", primary_key=True)
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)


class Blog(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    thumbnail_url: str | None = Field(default=None)
    content: str = Field(sa_column=Column(Text))
    author: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_public: bool = Field(default=True)
    likes: list["User"] = Relationship(
        back_populates="liked_blogs", link_model=BlogLikeLink
    )
    comments: list["Comment"] = Relationship(back_populates="blog")
    tags: list["Tag"] = Relationship(back_populates="blogs", link_model=BlogTagLink)


class Tag(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str | None = Field(default=None, unique=True, index=True)
    blogs: list[Blog] = Relationship(back_populates="tags", link_model=BlogTagLink)


class Comment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    content: str = Field(sa_column=Column(Text))
    commented_by: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_modified: datetime | None = Field(default=None)
    blog_id: int | None = Field(default=None, foreign_key="blog.id")
    blog: Blog | None = Relationship(back_populates="comments")


# to resolve string references for type checking
Blog.model_rebuild()
Comment.model_rebuild()
Tag.model_rebuild()
