from pydantic import BaseModel


class CommentsData(BaseModel):
    blog_id: int | None
    content: str
    commmented_by: str | None
    created_at: str | None

