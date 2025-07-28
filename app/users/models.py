from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import List

class UserFollowLink(SQLModel, table=True):
    follower_id: int | None = Field(default=None,foreign_key="user.id" ,primary_key=True)
    following_id: int | None = Field(default=None,foreign_key="user.id", primary_key=True)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True,)
    email: str = Field(unique=True, index=True)
    full_name: str = Field(default=None)
    joined_at: str | None= Field(default=datetime.now())
    hashed_password: str


    followings: List["User"] = Relationship(
        back_populates="followers",
        link_model=UserFollowLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowLink.follower_id",
            "secondaryjoin": "User.id==UserFollowLink.following_id" 
        }
    )

    followers: List["User"] = Relationship(
        back_populates="followings",
        link_model=UserFollowLink,
        sa_relationship_kwargs={
            "primaryjoin": "User.id==UserFollowLink.following_id",
            "secondaryjoin": "User.id==UserFollowLink.follower_id"
        }
    )
