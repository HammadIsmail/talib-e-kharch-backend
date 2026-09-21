from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import get_settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_pin, verify_pin
from app.models.category import Category
from app.models.user import User
from app.schemas.user import AuthResponse, RefreshTokenRequest, UserLogin, UserProfileUpdate, UserRegister, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()

DEFAULT_CATEGORIES = [
    ("Food & Canteen", "restaurant", 1),
    ("Transport", "directions_subway", 2),
    ("Academic", "school", 3),
    ("Personal", "shopping_bag", 4),
    ("Health", "local_hospital", 5),
    ("Entertainment", "sports_esports", 6),
    ("Utilities", "bolt", 7),
    ("Other", "more_horiz", 8),
]


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new student account with email and 4-6 digit PIN."""
    # Check if email exists
    result = await db.execute(select(User).where(User.email == req.email.lower()))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )

    now = datetime.now(timezone.utc)
    trial_ends = now + timedelta(days=settings.TRIAL_DAYS)

    new_user = User(
        name=req.name.strip(),
        email=req.email.lower().strip(),
        pin_hash=hash_pin(req.pin),
        tier="trial",
        trial_ends_at=trial_ends,
        currency="PKR",
        monthly_reset_day=1,
        daily_benchmark=1200.0,
    )
    db.add(new_user)
    await db.flush()

    # Seed default categories for this user
    for cat_name, icon, sort_ord in DEFAULT_CATEGORIES:
        category = Category(
            user_id=new_user.id,
            name=cat_name,
            icon=icon,
            is_default=True,
            sort_order=sort_ord,
        )
        db.add(category)

    await db.commit()
    await db.refresh(new_user)

    access_token = create_access_token(new_user.id)
    refresh_token = create_refresh_token(new_user.id)

    return AuthResponse(
        user=UserResponse.model_validate(new_user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login with email and PIN."""
    result = await db.execute(select(User).where(User.email == req.email.lower().strip()))
    user = result.scalar_one_or_none()

    if not user or not verify_pin(req.pin, user.pin_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or PIN",
        )

    # Check trial expiration
    now = datetime.now(timezone.utc)
    if user.tier == "trial" and user.trial_ends_at and user.trial_ends_at < now:
        user.tier = "free"
        db.add(user)
        await db.commit()
        await db.refresh(user)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh")
async def refresh_token(req: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Generate a new access token using a valid refresh token."""
    payload = decode_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_access_token = create_access_token(user.id)
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Return the profile of the authenticated user."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    req: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile settings (currency, reset day, daily benchmark, biometric, PIN)."""
    if req.name is not None:
        current_user.name = req.name.strip()
    if req.currency is not None:
        current_user.currency = req.currency
    if req.monthly_reset_day is not None:
        current_user.monthly_reset_day = req.monthly_reset_day
    if req.daily_benchmark is not None:
        current_user.daily_benchmark = req.daily_benchmark
    if req.biometric_enabled is not None:
        current_user.biometric_enabled = req.biometric_enabled
    if req.daily_digest is not None:
        current_user.daily_digest = req.daily_digest
    if req.voice_language is not None:
        current_user.voice_language = req.voice_language
    if req.pin is not None:
        current_user.pin_hash = hash_pin(req.pin)

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return UserResponse.model_validate(current_user)
