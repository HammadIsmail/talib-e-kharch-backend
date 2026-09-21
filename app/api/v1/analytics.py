import calendar
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.budget import Budget, BudgetEnvelope
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.analytics import DashboardAnalyticsResponse, EnvelopeProgress, RecentTransaction

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardAnalyticsResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Calculate core dashboard metrics for student finances."""
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_remaining = max(1, days_in_month - today.day + 1)

    # 1. Budget inflow
    budget_res = await db.execute(
        select(Budget)
        .options(selectinload(Budget.envelopes).selectinload(BudgetEnvelope.category))
        .where(
            Budget.user_id == current_user.id,
            Budget.month == today.month,
            Budget.year == today.year,
        )
    )
    budget = budget_res.scalar_one_or_none()
    total_inflow = budget.total_inflow if budget else 25000.0

    # 2. Month expenses
    month_exp_res = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.user_id == current_user.id,
            func.extract("month", Expense.expense_date) == today.month,
            func.extract("year", Expense.expense_date) == today.year,
        )
    )
    month_spent = float(month_exp_res.scalar() or 0.0)
    available_balance = max(0.0, total_inflow - month_spent)

    # 3. Safe Daily Spend
    safe_daily_spend = max(0.0, available_balance / days_remaining)

    # 4. Pace status
    expected_spend_to_date = (total_inflow / days_in_month) * today.day
    pace_percentage = round((month_spent / max(total_inflow, 1.0)) * 100, 1)

    if month_spent <= expected_spend_to_date * 1.05:
        pace_status = "Paced well"
    elif month_spent <= expected_spend_to_date * 1.25:
        pace_status = "Overspending risk"
    else:
        pace_status = "Critical crunch"

    # 5. Today's stats
    today_res = await db.execute(
        select(
            func.coalesce(func.sum(Expense.amount), 0.0),
            func.count(Expense.id),
        ).where(
            Expense.user_id == current_user.id,
            Expense.expense_date == today,
        )
    )
    today_spent, today_count = today_res.first() or (0.0, 0)

    # 6. Envelope progress
    envelopes_progress: list[EnvelopeProgress] = []
    if budget and budget.envelopes:
        for env in budget.envelopes:
            env_spent = 0.0
            if env.category_id:
                s_res = await db.execute(
                    select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
                        Expense.user_id == current_user.id,
                        Expense.category_id == env.category_id,
                        func.extract("month", Expense.expense_date) == today.month,
                        func.extract("year", Expense.expense_date) == today.year,
                    )
                )
                env_spent = float(s_res.scalar() or 0.0)
            icon = env.category.icon if env.category else "account_balance_wallet"
            if env.is_protected:
                icon = "lock"
            envelopes_progress.append(
                EnvelopeProgress(
                    name=env.name,
                    spent=env_spent,
                    allocated=env.allocated_amount,
                    icon=icon,
                    protected=env.is_protected,
                )
            )
    else:
        # Fallback default envelopes if user hasn't configured budget yet
        envelopes_progress = [
            EnvelopeProgress(name="Fixed Reserves", spent=0, allocated=12000, icon="lock", protected=True),
            EnvelopeProgress(name="Food & Canteen", spent=month_spent * 0.6, allocated=8000, icon="restaurant"),
            EnvelopeProgress(name="Transport", spent=month_spent * 0.3, allocated=3000, icon="directions_subway"),
        ]

    # 7. Recent transactions (latest 5)
    recent_res = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(Expense.user_id == current_user.id)
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
        .limit(5)
    )
    recent_expenses = recent_res.scalars().all()

    recent_txns = []
    for exp in recent_expenses:
        icon = exp.category.icon if exp.category else "receipt"
        cat_name = exp.category.name if exp.category else "General"
        time_str = exp.expense_time.strftime("%I:%M %p") if exp.expense_time else "Today"
        recent_txns.append(
            RecentTransaction(
                id=exp.id,
                description=exp.description,
                amount=exp.amount,
                category=cat_name,
                icon=icon,
                time=time_str,
                date=exp.expense_date.isoformat(),
            )
        )

    return DashboardAnalyticsResponse(
        available_balance=round(available_balance, 1),
        safe_daily_spend=round(safe_daily_spend, 1),
        days_remaining=days_remaining,
        total_inflow=round(total_inflow, 1),
        pace_percentage=pace_percentage,
        pace_status=pace_status,
        today_spent=round(float(today_spent), 1),
        today_count=int(today_count),
        envelopes=envelopes_progress,
        recent_transactions=recent_txns,
    )
