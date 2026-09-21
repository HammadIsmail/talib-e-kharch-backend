from datetime import date, datetime, time
from pydantic import BaseModel, Field

from app.schemas.category import CategoryResponse


class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0)
    description: str = Field(..., min_length=1, max_length=255)
    category_id: str | None = None
    expense_date: date = Field(default_factory=date.today)
    expense_time: time | None = None
    location: str | None = None
    source: str = "manual"  # manual, voice, ai


class ExpenseCreate(ExpenseBase):
    pass


class ExpenseUpdate(BaseModel):
    amount: float | None = Field(None, gt=0)
    description: str | None = Field(None, min_length=1, max_length=255)
    category_id: str | None = None
    expense_date: date | None = None
    expense_time: time | None = None
    location: str | None = None


class ExpenseResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    description: str
    category_id: str | None = None
    category: CategoryResponse | None = None
    source: str
    expense_date: date
    expense_time: time | None = None
    location: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    items: list[ExpenseResponse]
    total: int
    page: int
    pages: int
    total_amount: float
