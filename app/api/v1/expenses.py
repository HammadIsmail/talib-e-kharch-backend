from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models.category import Category
from app.models.expense import Expense
from app.models.user import User
from app.schemas.expense import ExpenseCreate, ExpenseListResponse, ExpenseResponse, ExpenseUpdate

router = APIRouter(prefix="/expenses", tags=["Expenses"])


@router.get("", response_model=ExpenseListResponse)
async def list_expenses(
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List expenses with filtering by date range, category, keyword, and pagination."""
    query = select(Expense).options(selectinload(Expense.category)).where(Expense.user_id == current_user.id)

    if date_from:
        query = query.where(Expense.expense_date >= date_from)
    if date_to:
        query = query.where(Expense.expense_date <= date_to)
    if category_id:
        query = query.where(Expense.category_id == category_id)
    if search:
        query = query.where(Expense.description.ilike(f"%{search}%"))

    # Total count and sum
    count_query = select(func.count(Expense.id), func.coalesce(func.sum(Expense.amount), 0.0)).where(
        Expense.user_id == current_user.id
    )
    if date_from:
        count_query = count_query.where(Expense.expense_date >= date_from)
    if date_to:
        count_query = count_query.where(Expense.expense_date <= date_to)
    if category_id:
        count_query = count_query.where(Expense.category_id == category_id)
    if search:
        count_query = count_query.where(Expense.description.ilike(f"%{search}%"))

    count_res = await db.execute(count_query)
    total_count, total_amount = count_res.first() or (0, 0.0)

    # Order and paginate
    query = query.order_by(Expense.expense_date.desc(), Expense.created_at.desc())
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    items = result.scalars().all()

    total_pages = max(1, (total_count + limit - 1) // limit)

    return ExpenseListResponse(
        items=[ExpenseResponse.model_validate(e) for e in items],
        total=total_count,
        page=page,
        pages=total_pages,
        total_amount=float(total_amount),
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    req: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Log an individual manual or parsed expense."""
    if req.category_id:
        cat_res = await db.execute(select(Category).where(Category.id == req.category_id))
        if not cat_res.scalar_one_or_none():
            req.category_id = None

    expense = Expense(
        user_id=current_user.id,
        amount=req.amount,
        description=req.description.strip(),
        category_id=req.category_id,
        expense_date=req.expense_date,
        expense_time=req.expense_time,
        location=req.location,
        source=req.source,
    )
    db.add(expense)
    await db.commit()
    await db.refresh(expense)

    # Eagerly fetch category for response
    res = await db.execute(
        select(Expense).options(selectinload(Expense.category)).where(Expense.id == expense.id)
    )
    loaded_expense = res.scalar_one()
    return ExpenseResponse.model_validate(loaded_expense)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: str,
    req: ExpenseUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing expense."""
    res = await db.execute(
        select(Expense)
        .options(selectinload(Expense.category))
        .where(Expense.id == expense_id, Expense.user_id == current_user.id)
    )
    expense = res.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    if req.amount is not None:
        expense.amount = req.amount
    if req.description is not None:
        expense.description = req.description.strip()
    if req.category_id is not None:
        expense.category_id = req.category_id
    if req.expense_date is not None:
        expense.expense_date = req.expense_date
    if req.expense_time is not None:
        expense.expense_time = req.expense_time
    if req.location is not None:
        expense.location = req.location

    db.add(expense)
    await db.commit()
    await db.refresh(expense)
    return ExpenseResponse.model_validate(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an expense."""
    res = await db.execute(
        select(Expense).where(Expense.id == expense_id, Expense.user_id == current_user.id)
    )
    expense = res.scalar_one_or_none()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    await db.delete(expense)
    await db.commit()
    return None
