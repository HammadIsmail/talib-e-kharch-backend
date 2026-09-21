from pydantic import BaseModel


class EnvelopeProgress(BaseModel):
    name: str
    spent: float
    allocated: float
    icon: str
    protected: bool = False


class RecentTransaction(BaseModel):
    id: str
    description: str
    amount: float
    category: str
    icon: str
    time: str
    date: str


class DashboardAnalyticsResponse(BaseModel):
    available_balance: float
    safe_daily_spend: float
    days_remaining: int
    total_inflow: float
    pace_percentage: float
    pace_status: str  # "Paced well", "Overspending risk", "Critical"
    today_spent: float
    today_count: int
    envelopes: list[EnvelopeProgress]
    recent_transactions: list[RecentTransaction]
