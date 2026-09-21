import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Budget(Base):
    """Monthly budget parent model."""

    __tablename__ = "budgets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-12
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_inflow: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user = relationship("User")
    envelopes = relationship("BudgetEnvelope", back_populates="budget", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("user_id", "month", "year", name="uq_user_month_year"),
    )


class BudgetEnvelope(Base):
    """Sub-allocation envelope within a monthly budget."""

    __tablename__ = "budget_envelopes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    budget_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("budgets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    allocated_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="flexible")  # fixed, flexible, reserve
    is_protected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    budget = relationship("Budget", back_populates="envelopes")
    category = relationship("Category", back_populates="budget_envelopes")
