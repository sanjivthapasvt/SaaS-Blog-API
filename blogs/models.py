from pydantic import BaseModel
class Blog(BaseModel):
    id: str | None
    title: str
    thumbnail: str | None
    content: str
    uploaded_by: str | None
    created_at: str | None
    modified_at: str | None

class Comments(BaseModel):
    id: str | None
    blog_id: int | None
    content: str
    commmented_by: str | None
    created_at: str | None
    modified_at: str | None