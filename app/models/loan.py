import enum
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LoanStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    closed = "closed"
    written_off = "written_off"


class Loan(Base):
    __tablename__ = "loans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    loan_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)

    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id"), nullable=False
    )
    loan_product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loan_products.id"), nullable=False
    )
    # FK to exactly one guarantor member; nullable if product doesn't require one.
    guarantor_member_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("members.id"), nullable=True
    )

    principal_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    security_provided_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    security_provided_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    deposit_paid_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    application_date: Mapped[date] = mapped_column(Date, nullable=False)
    disbursement_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[LoanStatus] = mapped_column(
        Enum(LoanStatus), nullable=False, default=LoanStatus.pending
    )
    outstanding_balance: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    member: Mapped["Member"] = relationship(  # type: ignore[name-defined]
        "Member", foreign_keys=[member_id]
    )
    guarantor: Mapped["Member | None"] = relationship(  # type: ignore[name-defined]
        "Member", foreign_keys=[guarantor_member_id]
    )
    loan_product: Mapped["LoanProduct"] = relationship(  # type: ignore[name-defined]
        "LoanProduct", back_populates="loans"
    )
    repayments: Mapped[list["Repayment"]] = relationship(  # type: ignore[name-defined]
        "Repayment", back_populates="loan", order_by="Repayment.payment_date"
    )
    ledger_transactions: Mapped[list["LedgerTransaction"]] = relationship(  # type: ignore[name-defined]
        "LedgerTransaction", back_populates="related_loan"
    )
