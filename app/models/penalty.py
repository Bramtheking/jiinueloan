"""
LoanProductPenalty — penalty library per loan product.
Multiple penalties can be attached to one product (unlike the single late_payment_penalty).
"""

import enum
from decimal import Decimal

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PenaltyTrigger(str, enum.Enum):
    late_payment = "late_payment"         # triggered when payment is past due date
    missed_payment = "missed_payment"     # triggered when a period is fully missed
    meeting_absence = "meeting_absence"   # custom — e.g. SACCO meeting fine


class PenaltyBasis(str, enum.Enum):
    fixed_amount = "fixed_amount"
    percent_of_balance = "percent_of_balance"
    percent_of_principal = "percent_of_principal"


class LoanProductPenalty(Base):
    __tablename__ = "loan_product_penalties"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    loan_product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loan_products.id", ondelete="CASCADE"), nullable=False, index=True
    )

    penalty_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger: Mapped[PenaltyTrigger] = mapped_column(Enum(PenaltyTrigger), nullable=False)
    basis: Mapped[PenaltyBasis] = mapped_column(Enum(PenaltyBasis), nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ledger_account_name: Mapped[str] = mapped_column(String(255), nullable=False)

    product: Mapped["LoanProduct"] = relationship(  # type: ignore[name-defined]
        "LoanProduct", back_populates="penalties"
    )
