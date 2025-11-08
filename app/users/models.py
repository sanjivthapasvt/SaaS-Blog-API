import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import (TIMESTAMP, Column, Field, Relationship, SQLModel, Text,
                      func)
from sqlalchemy.orm import Mapped

from app.models.blog_like_link import BlogLikeLink

if TYPE_CHECKING:
    from blogs.models import Blog


class UserFollowLink(SQLModel, table=True):
    follower_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    following_id: Optional[int] = Field(
        default=None, foreign_key="user.id", primary_key=True, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uuid: str = Field(
        default_factory=lambda: str(uuid.uuid4()), index=True, unique=True
    )
    profile_pic: Optional[str] = Field(
        default=None,
    )
    google_id: Optional[str] = Field(default=None, unique=True, index=True)
    username: Optional[str] = Field(unique=True, index=True, max_length=50)
    email: str = Field(unique=True, index=True)
    full_name: str = Field(default=None)
    bio: Optional[str] = Field(default=None, sa_column=Column(Text))
    joined_at: datetime = Field(
        default=None,
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now()),
    )
    hashed_password: Optional[str] = None
    is_active: bool = Field(default=True)
    
    is_superuser: bool = Field(default=False)

    liked_blogs: Mapped[List["Blog"]] = Relationship(
        back_populates="likes", link_model=BlogLikeLink, cascade_delete=True
    )

    followings: Mapped[List["User"]] = Relationship(
        back_populates="followers",
        link_model=UserFollowLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowLink.follower_id",
            "secondaryjoin": "User.id==UserFollowLink.following_id",
            "overlaps": "followers",
        },
        cascade_delete=True
    )

    followers: Mapped[List["User"]] = Relationship(
        back_populates="followings",
        link_model=UserFollowLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowLink.following_id",
            "secondaryjoin": "User.id==UserFollowLink.follower_id",
            "overlaps": "followings",
        },
        cascade_delete=True
    )


class BookMark(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True, ondelete="CASCADE")
    blog_id: int = Field(foreign_key="blog.id", primary_key=True, ondelete="CASCADE")


User.model_rebuild()
from app.blogs.models import Blog
Blog.model_rebuild()