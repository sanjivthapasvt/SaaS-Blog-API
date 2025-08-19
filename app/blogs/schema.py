from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class BlogResponse(BaseModel):
    id: int
    title: str
    thumbnail_url: str | None
    author: int
    tags: list[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BlogContentResponse(BaseModel):
    id: int
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
