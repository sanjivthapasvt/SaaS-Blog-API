from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class BlogResponse(BaseModel):
    id: int
    title: str
    slug: str
    thumbnail_url: str | None
    author: int
    tags: list[str]
    created_at: datetime
    likes_count: int
    comments_count: int
    bookmarks_count: int 
    views: int
    
    model_config = ConfigDict(from_attributes=True)


class BlogContentResponse(BaseModel):
    title: str
    content: str
    author: int
    created_at: datetime


class CommentData(BaseModel):
    blog_id: int
    content: str
    commmented_by: int
    created_at: datetime


class CommentWrite(BaseModel):
    content: Annotated[str, StringConstraints(min_length=1, max_length=500)]
