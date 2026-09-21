from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.budget import Budget, BudgetEnvelope
from app.models.expense import Expense
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate, EnvelopeCreate, EnvelopeResponse

router = APIRouter(prefix="/budgets", tags=["Budgets"])


@router.get("/current", response_model=BudgetResponse)
async def get_current_budget(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the active monthly budget and envelopes with real-time spent calculation."""
    today = date.today()
    return await _get_or_create_monthly_budget(current_user, today.month, today.year, db)


@router.get("/{year}/{month}", response_model=BudgetResponse)
async def get_budget_by_month(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get budget for a specific month and year."""
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Invalid month (must be 1-12)")
    return await _get_or_create_monthly_budget(current_user, month, year, db)


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def set_budget(
    req: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or overwrite monthly budget total stipend and envelopes."""
    res = await db.execute(
        select(Budget)
        .options(selectinload(Budget.envelopes).selectinload(BudgetEnvelope.category))
        .where(
            Budget.user_id == current_user.id,
            Budget.month == req.month,
            Budget.year == req.year,
        )
    )
    budget = res.scalar_one_or_none()

    if not budget:
        budget = Budget(
            user_id=current_user.id,
            month=req.month,
            year=req.year,
            total_inflow=req.total_inflow,
        )
        db.add(budget)
        await db.flush()
    else:
        budget.total_inflow = req.total_inflow
        # Remove existing envelopes to replace
        for env in budget.envelopes:
            await db.delete(env)
        await db.flush()

    # Add provided envelopes
    for env_data in req.envelopes:
        envelope = BudgetEnvelope(
            budget_id=budget.id,
            category_id=env_data.category_id,
            name=env_data.name,
            allocated_amount=env_data.allocated_amount,
            type=env_data.type,
            is_protected=env_data.is_protected,
        )
        db.add(envelope)

    await db.commit()
    return await _get_or_create_monthly_budget(current_user, req.month, req.year, db)


@router.post("/{budget_id}/envelopes", response_model=EnvelopeResponse)
async def add_envelope(
    budget_id: str,
    req: EnvelopeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a new envelope to an existing budget."""
    res = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    )
    budget = res.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    envelope = BudgetEnvelope(
        budget_id=budget.id,
        category_id=req.category_id,
        name=req.name,
        allocated_amount=req.allocated_amount,
        type=req.type,
        is_protected=req.is_protected,
    )
    db.add(envelope)
    await db.commit()
    await db.refresh(envelope)
    return EnvelopeResponse.model_validate(envelope)


async def _get_or_create_monthly_budget(
    user: User, month: int, year: int, db: AsyncSession
) -> BudgetResponse:
    res = await db.execute(
        select(Budget)
        .options(selectinload(Budget.envelopes).selectinload(BudgetEnvelope.category))
        .where(Budget.user_id == user.id, Budget.month == month, Budget.year == year)
    )
    budget = res.scalar_one_or_none()

    if not budget:
        # Default empty budget with initial allocation
        budget = Budget(
            user_id=user.id,
            month=month,
            year=year,
            total_inflow=25000.0,  # sensible Pakistani student default
        )
        db.add(budget)
        await db.flush()

        # Create sensible default envelopes
        defaults = [
            ("Fixed Reserves (Hostel / Fees)", 12000.0, "reserve", True),
            ("Food & Canteen", 8000.0, "flexible", False),
            ("Transport & Metro", 3000.0, "flexible", False),
            ("Academic & Printing", 2000.0, "flexible", False),
        ]
        for name, amt, typ, prot in defaults:
            env = BudgetEnvelope(
                budget_id=budget.id,
                name=name,
                allocated_amount=amt,
                type=typ,
                is_protected=prot,
            )
            db.add(env)
        await db.commit()

        # Reload with relations
        res = await db.execute(
            select(Budget)
            .options(selectinload(Budget.envelopes).selectinload(BudgetEnvelope.category))
            .where(Budget.id == budget.id)
        )
        budget = res.scalar_one()

    # Calculate spent amounts for envelopes
    envelope_responses: list[EnvelopeResponse] = []
    total_allocated = 0.0

    for env in budget.envelopes:
        total_allocated += env.allocated_amount
        spent = 0.0
        if env.category_id:
            exp_res = await db.execute(
                select(func.coalesce(func.sum(Expense.amount), 0.0)).where(
                    Expense.user_id == user.id,
                    Expense.category_id == env.category_id,
                    func.extract("month", Expense.expense_date) == month,
                    func.extract("year", Expense.expense_date) == year,
                )
            )
            spent = float(exp_res.scalar() or 0.0)

        envelope_responses.append(
            EnvelopeResponse(
                id=env.id,
                budget_id=env.budget_id,
                category_id=env.category_id,
                name=env.name,
                allocated_amount=env.allocated_amount,
                type=env.type,
                is_protected=env.is_protected,
                spent_amount=spent,
                category=env.category,
                created_at=env.created_at,
            )
        )

    return BudgetResponse(
        id=budget.id,
        user_id=budget.user_id,
        month=budget.month,
        year=budget.year,
        total_inflow=budget.total_inflow,
        total_allocated=total_allocated,
        unallocated=max(0.0, budget.total_inflow - total_allocated),
        envelopes=envelope_responses,
        created_at=budget.created_at,
        updated_at=budget.updated_at,
    )
