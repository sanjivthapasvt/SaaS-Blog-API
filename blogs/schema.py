from pydantic import BaseModel

class BlogRead(BaseModel):
    id:int
    title: str
    thumbnail_url: str | None
    content: str
    uploaded_by: int
    created_at: str
    
class CommentsData(BaseModel):
    blog_id: int | None
    content: str
    commmented_by: str | None
    created_at: str | None

