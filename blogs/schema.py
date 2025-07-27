from datetime import datetime
from sqlmodel import SQLModel, Field

class Blog(SQLModel):
    id: str | None = Field(default=None, primary_key=True)
    title: str
    thumbnail: str
    content: str
    uploaded_by: str
    created_at: str
    modified_at: str