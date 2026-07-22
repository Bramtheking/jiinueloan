"""
Loan product models.

Versioning design:
- Each edit to a product creates a NEW row (version_number incremented).
- The old row is set is_active=False but is never deleted.
- Loans store a FK to loan_products.id (the specific version row), so rate
  changes never retroactively affect already-issued loans.
- The "active" version of a product_code is the row where is_active=True.
  Only one row per product_code should be active at any time (enforced in CRUD).
"""

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


class InterestMethod(str, enum.Enum):
    flat = "flat"
    reducing_balance = "reducing_balance"
    compound = "compound"


class InterestPeriod(str, enum.Enum):
    monthly = "monthly"
    yearly = "yearly"


class RepaymentFrequency(str, enum.Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    yearly = "yearly"


class SecurityType(str, enum.Enum):
    percentage = "percentage"
    fixed_amount = "fixed_amount"
    custom_text = "custom_text"


class FeeType(str, enum.Enum):
    percentage = "percentage"
    fixed_amount = "fixed_amount"


class DepositType(str, enum.Enum):
    percentage = "percentage"
    fixed_amount = "fixed_amount"


class LatePaymentPenaltyType(str, enum.Enum):
    percentage = "percentage"
    fixed_amount = "fixed_amount"


class OffsetCoverType(str, enum.Enum):
    savings = "savings"
    security = "security"
    both = "both"


class LoanProduct(Base):
    __tablename__ = "loan_products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Interest
    interest_method: Mapped[InterestMethod] = mapped_column(
        Enum(InterestMethod), nullable=False
    )
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    interest_period: Mapped[InterestPeriod] = mapped_column(
        Enum(InterestPeriod), nullable=False
    )

    # Repayment schedule
    repayment_frequency: Mapped[RepaymentFrequency] = mapped_column(
        Enum(RepaymentFrequency), nullable=False
    )
    max_repayment_period: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Guarantor
    requires_guarantor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Savings multiple
    is_multiple_of_savings: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    savings_multiplier: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)

    # Security
    requires_security: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    security_type: Mapped[SecurityType | None] = mapped_column(
        Enum(SecurityType), nullable=True
    )
    security_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    security_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Deposit
    requires_deposit: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deposit_type: Mapped[DepositType | None] = mapped_column(Enum(DepositType), nullable=True)
    deposit_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # Repayment allocation order (comma-separated priority)
    # e.g. "penalty,interest,principal" or "interest,penalty,principal"
    allocation_order: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default="penalty,interest,principal"
    )

    # Late payment penalty (legacy single-penalty; new multi-penalty via LoanProductPenalty)
    late_payment_penalty_type: Mapped[LatePaymentPenaltyType | None] = mapped_column(
        Enum(LatePaymentPenaltyType), nullable=True
    )
    late_payment_penalty_value: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )

    # -----------------------------------------------------------------------
    # Approval workflow
    # -----------------------------------------------------------------------
    requires_appraisal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_board_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # -----------------------------------------------------------------------
    # Aging / status thresholds (days overdue)
    # -----------------------------------------------------------------------
    watchful_after_days: Mapped[int | None] = mapped_column(Integer, nullable=True, default=30)
    non_performing_after_days: Mapped[int | None] = mapped_column(Integer, nullable=True, default=90)
    doubtful_after_days: Mapped[int | None] = mapped_column(Integer, nullable=True, default=180)

    # -----------------------------------------------------------------------
    # Rescheduling
    # -----------------------------------------------------------------------
    allows_rescheduling: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reschedule_fee_type: Mapped[LatePaymentPenaltyType | None] = mapped_column(
        Enum(LatePaymentPenaltyType), nullable=True
    )
    reschedule_fee_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    # -----------------------------------------------------------------------
    # Offset
    # -----------------------------------------------------------------------
    allows_offset: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    offset_covers: Mapped[OffsetCoverType | None] = mapped_column(
        Enum(OffsetCoverType), nullable=True
    )
    offset_fee_type: Mapped[LatePaymentPenaltyType | None] = mapped_column(
        Enum(LatePaymentPenaltyType), nullable=True
    )
    offset_fee_value: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    fees: Mapped[list["LoanProductFee"]] = relationship(
        "LoanProductFee", back_populates="product", cascade="all, delete-orphan"
    )
    penalties: Mapped[list["LoanProductPenalty"]] = relationship(  # type: ignore[name-defined]
        "LoanProductPenalty", back_populates="product", cascade="all, delete-orphan"
    )
    loans: Mapped[list["Loan"]] = relationship("Loan", back_populates="loan_product")  # type: ignore[name-defined]


class LoanProductFee(Base):
    __tablename__ = "loan_product_fees"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    loan_product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("loan_products.id", ondelete="CASCADE"), nullable=False
    )
    fee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    fee_type: Mapped[FeeType] = mapped_column(Enum(FeeType), nullable=False)
    fee_value: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)
    # What the percentage is calculated on (only relevant when fee_type=percentage)
    fee_basis: Mapped[str | None] = mapped_column(String(50), nullable=True, default="principal")
    # Options: "principal" | "savings" | "deposit" | "loan_balance"
    affects_principal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    show_in_statement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ledger_account_name: Mapped[str] = mapped_column(String(255), nullable=False)

    product: Mapped["LoanProduct"] = relationship("LoanProduct", back_populates="fees")
