from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from nanoid import generate
from slugify import slugify
from sqlmodel import (TIMESTAMP, Column, Field, Relationship, SQLModel, Text,
                      func)

from app.models.blog_like_link import BlogLikeLink

if TYPE_CHECKING:
    from users.models import User


class BlogTagLink(SQLModel, table=True):
    blog_id: Optional[int] = Field(
        default=None, foreign_key="blog.id", primary_key=True
    )
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)


class Blog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True, max_length=500)
    slug: str | None = Field(default=None, index=True, unique=True)
    thumbnail_url: str | None = Field(default=None)
    content: str = Field(sa_column=Column(Text))
    author: int = Field(foreign_key="user.id")
    created_at: datetime = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now()),
    )
    is_public: bool = Field(default=True)
    likes: list["User"] = Relationship(
        back_populates="liked_blogs", link_model=BlogLikeLink
    )
    comments: list["Comment"] = Relationship(back_populates="blog")
    tags: list["Tag"] = Relationship(back_populates="blogs", link_model=BlogTagLink)

    def generate_slug(self):
        if not self.slug:
            self.slug = slugify(f"{self.title}-{generate(size=10)}")


class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: Optional[str] = Field(default=None, unique=True, index=True)
    blogs: list[Blog] = Relationship(back_populates="tags", link_model=BlogTagLink)


class Comment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(sa_column=Column(Text))
    commented_by: int | None = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now()),
    )
    last_modified: datetime | None = Field(default=None)
    blog_id: int = Field(foreign_key="blog.id", index=True)
    blog: Optional[Blog] = Relationship(back_populates="comments")


# to resolve string references for type checking
Blog.model_rebuild()
Comment.model_rebuild()
Tag.model_rebuild()
