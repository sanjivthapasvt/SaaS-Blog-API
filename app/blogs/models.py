from datetime import datetime
from typing import TYPE_CHECKING, Optional

from nanoid import generate
from slugify import slugify
from sqlalchemy import event as sa_event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapper
from sqlmodel import (TIMESTAMP, Column, Field, Relationship, SQLModel, Text,
                      func)

from app.models.blog_like_link import BlogLikeLink

if TYPE_CHECKING:
    from app.users.models import User


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

    # Counters for like, comment, bookmarks, views
    likes_count: int = Field(default=0)
    comments_count: int = Field(default=0)
    bookmarks_count: int = Field(default=0)
    views_count: int = Field(default=0)

    # Score for engagemnet, trending and popular
    engagement_score: float = Field(default=0, index=True)

    def update_engagement_score(self) -> None:
        """Update engagement score"""
        self.engagement_score = (
            self.likes_count * 1.0
            + self.comments_count * 3.0
            + self.bookmarks_count * 2.0
            + self.views_count * 0.1
        )


# Generate slug whenever new blog is inserted
@sa_event.listens_for(Blog, "before_insert")
def generate_slug(mapper: Mapper[Blog], connection: Connection, target: Blog):
    if not target.slug and target.title:
        target.slug = slugify(f"{target.title}-{generate(size=10)}")


# Realtime update for engagement_score
@sa_event.listens_for(Blog, "before_update")
def update_engagement_score_realtime(
    mapper: Mapper[Blog], connection: Connection, target: Blog
):
    """
    Automatically update engagement score before saving blog changes.
    """
    target.update_engagement_score()


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
