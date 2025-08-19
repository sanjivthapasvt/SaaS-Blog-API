from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    limit: int
    offset: int
    data: List[T]


class CommonParams(BaseModel):
    search: str | None
    limit: int
    offset: int
