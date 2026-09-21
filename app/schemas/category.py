from datetime import datetime
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    icon: str = Field("restaurant", max_length=50)
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: str
    user_id: str | None = None
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True
