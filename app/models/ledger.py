from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LedgerTransaction(Base):
    """
    Simple Money-In / Money-Out ledger per named account.

    Reversal design:
    - Reversing a transaction does NOT edit the original row.
    - Instead, a new offsetting row is created with is_reversed=False,
      and reversal_of_transaction_id pointing to the original.
    - The original row is marked is_reversed=True.
    - This preserves full history.
    """

    __tablename__ = "ledger_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    money_in: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    money_out: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    related_loan_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("loans.id"), nullable=True, index=True
    )
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)

    is_reversed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reversal_of_transaction_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("ledger_transactions.id", use_alter=True, name="fk_reversal_self"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    related_loan: Mapped["Loan | None"] = relationship(  # type: ignore[name-defined]
        "Loan", back_populates="ledger_transactions"
    )
    reversal_source: Mapped["LedgerTransaction | None"] = relationship(
        "LedgerTransaction",
        foreign_keys=[reversal_of_transaction_id],
        remote_side=[id],
    )
