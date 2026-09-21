from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all categories available to user (user-specific + system defaults)."""
    result = await db.execute(
        select(Category)
        .where(or_(Category.user_id == current_user.id, Category.user_id.is_(None)))
        .order_by(Category.sort_order.asc(), Category.name.asc())
    )
    categories = result.scalars().all()
    return [CategoryResponse.model_validate(c) for c in categories]


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    req: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom category."""
    category = Category(
        user_id=current_user.id,
        name=req.name.strip(),
        icon=req.icon,
        sort_order=req.sort_order,
        is_default=False,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return CategoryResponse.model_validate(category)
