from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, StringConstraints


class UserCreate(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)]
    first_name: Annotated[str, StringConstraints(min_length=3, max_length=20)]
    last_name: Annotated[str, StringConstraints(min_length=3, max_length=25)]
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=250)]


class UserUpdate(BaseModel):
    username: Annotated[str, StringConstraints(min_length=3, max_length=50)] | None
    full_name: Annotated[str, StringConstraints(min_length=5, max_length=100)] | None
    password: Annotated[str, StringConstraints(min_length=8, max_length=250)] | None
    is_active: bool | None
    is_superuser: bool | None


class UserDetail(BaseModel):
    username: str | None
    full_name: str | None
    profile_pic: str | None
    email: str | None
    bio: str | None
    joined_at: datetime
    is_active: bool
    is_superuser: bool


# Blog Schemas
class BlogCreate(BaseModel):
    title: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    content: str
    is_public: bool = True
    thumbnail_url: str | None = None


class BlogUpdate(BaseModel):
    title: Annotated[str, StringConstraints(min_length=1, max_length=500)] | None = None
    content: str | None = None
    is_public: bool | None = None
    thumbnail_url: str | None = None
    engagement_score: float | None = None


class BlogDetail(BaseModel):
    id: int
    title: str
    slug: str | None
    thumbnail_url: str | None
    content: str
    author: int
    created_at: datetime
    is_public: bool
    likes_count: int
    comments_count: int
    bookmarks_count: int
    views: int
    engagement_score: float


# Tag Schemas
class TagCreate(BaseModel):
    title: Annotated[str, StringConstraints(min_length=1, max_length=50)]


class TagUpdate(BaseModel):
    title: Annotated[str, StringConstraints(min_length=1, max_length=50)] | None = None


class TagDetail(BaseModel):
    id: int
    title: str | None


# Comment Schemas
class CommentUpdate(BaseModel):
    content: str


class CommentDetail(BaseModel):
    id: int
    content: str
    commented_by: int | None
    created_at: datetime
    last_modified: datetime | None
    blog_id: int


# Notification Schemas
class NotificationCreate(BaseModel):
    owner_id: int
    blog_id: int | None = None
    triggered_by_user_id: int
    notification_type: str
    message: str


class NotificationDetail(BaseModel):
    id: int
    owner_id: int
    blog_id: int | None
    triggered_by_user_id: int
    notification_type: str
    message: str
    created_at: datetime
    is_read: bool
