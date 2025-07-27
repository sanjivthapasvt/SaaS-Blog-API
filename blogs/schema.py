from pydantic import BaseModel
class BlogCreate(BaseModel):
    title: str
    thumbnail: str | None
    content: str

class CommentsData(BaseModel):
    id: str | None
    blog_id: int | None
    content: str
    commmented_by: str | None
    created_at: str | None

class BlogCreated(BaseModel):
    title: str
    detail: str