from datetime import datetime
from pydantic import BaseModel, Field

from app.schemas.category import CategoryResponse


class EnvelopeBase(BaseModel):
    category_id: str | None = None
    name: str = Field(..., min_length=1, max_length=100)
    allocated_amount: float = Field(..., ge=0)
    type: str = Field("flexible", pattern=r"^(fixed|flexible|reserve)$")
    is_protected: bool = False


class EnvelopeCreate(EnvelopeBase):
    pass


class EnvelopeResponse(EnvelopeBase):
    id: str
    budget_id: str
    spent_amount: float = 0.0
    category: CategoryResponse | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class BudgetCreate(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2024, le=2100)
    total_inflow: float = Field(..., ge=0)
    envelopes: list[EnvelopeCreate] = []


class BudgetUpdate(BaseModel):
    total_inflow: float | None = Field(None, ge=0)


class BudgetResponse(BaseModel):
    id: str
    user_id: str
    month: int
    year: int
    total_inflow: float
    total_allocated: float = 0.0
    unallocated: float = 0.0
    envelopes: list[EnvelopeResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
