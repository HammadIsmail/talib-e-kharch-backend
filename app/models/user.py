import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    tier: Mapped[str] = mapped_column(String(20), nullable=False, default="trial")
    trial_ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="PKR")
    monthly_reset_day: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    daily_benchmark: Mapped[float] = mapped_column(Float, nullable=False, default=1200.0)
    biometric_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    daily_digest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    voice_language: Mapped[str] = mapped_column(String(10), nullable=False, default="both")
    revenuecat_id: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
