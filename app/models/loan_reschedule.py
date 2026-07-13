"""
LoanReschedule — records every rescheduling event for a loan.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LoanReschedule(Base):
    __tablename__ = "loan_reschedules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    loan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reschedule_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Snapshot before reschedule
    old_num_periods: Mapped[int] = mapped_column(Integer, nullable=False)
    old_outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # New configuration
    new_num_periods: Mapped[int] = mapped_column(Integer, nullable=False)
    new_installment: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Fee charged for rescheduling (if product configured one)
    fee_charged: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    loan: Mapped["Loan"] = relationship("Loan", back_populates="reschedules")  # type: ignore[name-defined]
