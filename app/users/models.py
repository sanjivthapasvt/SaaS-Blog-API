from sqlmodel import SQLModel, Field, Relationship
from datetime import timezone, datetime
from typing import List

class UserFollowLink(SQLModel, table=True):
    follower_id: int | None = Field(default=None,foreign_key="user.id" ,primary_key=True)
    following_id: int | None = Field(default=None,foreign_key="user.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    google_id: str | None = Field(default=None, unique=True)
    username: str | None = Field(unique=True, index=True,)
    email: str = Field(unique=True, index=True)
    full_name: str = Field(default=None)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    hashed_password: str| None = None
    is_active: bool = True

    followings: List["User"] = Relationship(
        back_populates="followers",
        link_model=UserFollowLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowLink.follower_id",
            "secondaryjoin": "User.id==UserFollowLink.following_id",
            "overlaps": "followers",
        }
    )

    followers: List["User"] = Relationship(
        back_populates="followings",
        link_model=UserFollowLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowLink.following_id",
            "secondaryjoin": "User.id==UserFollowLink.follower_id",
            "overlaps": "followings"
        }
    )
