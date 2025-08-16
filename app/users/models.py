from datetime import datetime, timezone
from typing import TYPE_CHECKING, List

from sqlmodel import Field, Relationship, SQLModel

from app.models.blog_like_link import BlogLikeLink

if TYPE_CHECKING:
    from blogs.models import Blog


class UserFollowLink(SQLModel, table=True):
    follower_id: int | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    following_id: int | None = Field(
        default=None, foreign_key="user.id", primary_key=True
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    profile_pic: str | None = Field(
        default=None,
    )
    google_id: str | None = Field(default=None, unique=True, index=True)
    username: str | None = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    full_name: str = Field(default=None)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hashed_password: str | None = None
    is_active: bool = Field(default=True)

    liked_blogs: list["Blog"] = Relationship(
        back_populates="likes", link_model=BlogLikeLink
    )

    followings: List["User"] = Relationship(
        back_populates="followers",
        link_model=UserFollowLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowLink.follower_id",
            "secondaryjoin": "User.id==UserFollowLink.following_id",
            "overlaps": "followers",
        },
    )

    followers: List["User"] = Relationship(
        back_populates="followings",
        link_model=UserFollowLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowLink.following_id",
            "secondaryjoin": "User.id==UserFollowLink.follower_id",
            "overlaps": "followings",
        },
    )


User.model_rebuild()
