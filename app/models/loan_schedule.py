"""
Loan schedule entry — one row per expected repayment period.
Generated when a loan is disbursed. Cancelled and regenerated on rescheduling.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LoanScheduleEntry(Base):
    __tablename__ = "loan_schedule_entries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    loan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True
    )

    period_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    expected_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    expected_principal: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    expected_interest: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    closing_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Tracking
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_missed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    amount_actually_paid: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    loan: Mapped["Loan"] = relationship("Loan", back_populates="schedule_entries")  # type: ignore[name-defined]
