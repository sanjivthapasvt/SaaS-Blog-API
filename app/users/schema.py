from pydantic import BaseModel

class UserRead(BaseModel):
    id: int
    full_name: str