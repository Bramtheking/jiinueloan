from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Repayment(Base):
    __tablename__ = "repayments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    loan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loans.id"), nullable=False, index=True
    )
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)

    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Breakdown calculated by the repayment engine (penalty → interest → principal order)
    amount_to_penalty: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    amount_to_interest: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    amount_to_principal: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    remaining_balance_after: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # Credit scoring hooks — flags only, no scoring logic built yet
    is_underpaid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_overpaid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    loan: Mapped["Loan"] = relationship("Loan", back_populates="repayments")  # type: ignore[name-defined]
