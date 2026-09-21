import calendar
from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_premium_or_trial
from app.models.budget import Budget
from app.models.expense import Expense
from app.models.user import User
from app.schemas.ai import (
    AffordabilityRequest,
    AffordabilityResponse,
    VoiceExpenseImpact,
    VoiceExpenseRequest,
    VoiceExpenseResponse,
    VoiceSessionResponse,
)
from app.services.gemini_service import evaluate_affordability, parse_expense_with_gemini
from app.services.uplift_service import create_uplift_voice_session

router = APIRouter(prefix="/ai", tags=["AI & Voice"])


@router.post("/parse-expense", response_model=VoiceExpenseResponse)
async def parse_voice_expense(
    req: VoiceExpenseRequest,
    current_user: User = Depends(require_premium_or_trial),
    db: AsyncSession = Depends(get_db),
):
    """Parse Roman Urdu or English transcript into structured expenses using Gemini 1.5 Flash."""
    parsed = await parse_expense_with_gemini(req.text)
    total = sum(p.amount for p in parsed)

    # Calculate impact on daily safe spend
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_remaining = max(1, days_in_month - today.day)

    # Current budget & expenses
    budget_res = await db.execute(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.month == today.month,
            Budget.year == today.year,
        )
    )
    budget = budget_res.scalar_one_or_none()
    inflow = budget.total_inflow if budget else 25000.0

    exp_res = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.user_id == current_user.id,
            func.extract("month", Expense.expense_date) == today.month,
            func.extract("year", Expense.expense_date) == today.year,
        )
    )
    spent = float(exp_res.scalar() or 0.0)

    remaining_cash = max(0.0, inflow - spent)
    current_safe_daily = remaining_cash / days_remaining
    new_safe_daily = max(0.0, (remaining_cash - total) / days_remaining)

    impact = VoiceExpenseImpact(
        current_safe_daily=round(current_safe_daily, 1),
        new_safe_daily=round(new_safe_daily, 1),
        days_remaining=days_remaining,
    )

    return VoiceExpenseResponse(
        parsed_items=parsed,
        total=total,
        impact=impact,
    )


@router.post("/affordability", response_model=AffordabilityResponse)
async def check_affordability(
    req: AffordabilityRequest,
    current_user: User = Depends(require_premium_or_trial),
    db: AsyncSession = Depends(get_db),
):
    """Evaluate whether an item is safe to buy without jeopardizing essential student expenses."""
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]
    days_remaining = max(1, days_in_month - today.day)

    budget_res = await db.execute(
        select(Budget).where(
            Budget.user_id == current_user.id,
            Budget.month == today.month,
            Budget.year == today.year,
        )
    )
    budget = budget_res.scalar_one_or_none()
    inflow = budget.total_inflow if budget else 25000.0

    exp_res = await db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
            Expense.user_id == current_user.id,
            func.extract("month", Expense.expense_date) == today.month,
            func.extract("year", Expense.expense_date) == today.year,
        )
    )
    spent = float(exp_res.scalar() or 0.0)
    remaining_balance = max(0.0, inflow - spent)
    safe_daily = remaining_balance / days_remaining

    return await evaluate_affordability(
        query=req.query,
        amount=req.amount,
        current_balance=remaining_balance,
        safe_daily=safe_daily,
        days_left=days_remaining,
    )


@router.post("/voice-session", response_model=VoiceSessionResponse)
async def get_voice_session(
    current_user: User = Depends(require_premium_or_trial),
):
    """Get active session token for Uplift AI Voice STT/TTS (prime-time-anchor)."""
    return await create_uplift_voice_session(current_user.id)
