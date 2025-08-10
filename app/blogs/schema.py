from pydantic import BaseModel
from datetime import datetime

class BlogResponse(BaseModel):
    id:int
    title: str
    thumbnail_url: str | None
    author: int
    tags: list[str]
    created_at: datetime
    
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
