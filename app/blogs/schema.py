from pydantic import BaseModel
from datetime import datetime

class BlogResponse(BaseModel):
    id:int
    title: str
    thumbnail_url: str | None
    content: str
    uploaded_by: int
    tags: list[str]
    created_at: datetime
    

class CommentData(BaseModel):
    blog_id: int
    content: str
    commmented_by: int
    created_at: datetime
