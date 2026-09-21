import uuid
from datetime import date, datetime, time, timezone
from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Expense(Base):
    """Expense transaction model."""

    __tablename__ = "expenses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")  # manual, voice, ai
    expense_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today, index=True)
    expense_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = relationship("User")
    category = relationship("Category", back_populates="expenses")

    __table_args__ = (
        Index("idx_user_expense_date", "user_id", "expense_date"),
        Index("idx_user_category", "user_id", "category_id"),
    )
