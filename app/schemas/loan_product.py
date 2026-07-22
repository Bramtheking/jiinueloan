from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel

from app.models.loan_product import (
    InterestMethod,
    InterestPeriod,
    RepaymentFrequency,
    SecurityType,
    FeeType,
    DepositType,
    LatePaymentPenaltyType,
    OffsetCoverType,
)
from app.models.penalty import PenaltyTrigger, PenaltyBasis


# ---------------------------------------------------------------------------
# Loan Product Fee Schemas
# ---------------------------------------------------------------------------

class LoanProductFeeCreate(BaseModel):
    fee_name: str
    fee_type: FeeType
    fee_value: Decimal
    fee_basis: Optional[str] = "principal"
    affects_principal: bool = False
    show_in_statement: bool = True
    ledger_account_name: str


class LoanProductFeeRead(LoanProductFeeCreate):
    id: int
    loan_product_id: int
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Loan Product Penalty Schemas
# ---------------------------------------------------------------------------

class LoanProductPenaltyCreate(BaseModel):
    penalty_name: str
    trigger: PenaltyTrigger
    basis: PenaltyBasis
    value: Decimal
    is_active: bool = True
    ledger_account_name: str


class LoanProductPenaltyRead(LoanProductPenaltyCreate):
    id: int
    loan_product_id: int
    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Loan Product Schemas
# ---------------------------------------------------------------------------

class LoanProductCreate(BaseModel):
    product_code: str
    product_name: str
    effective_date: date
    interest_method: InterestMethod
    interest_rate: Decimal
    interest_period: InterestPeriod
    repayment_frequency: RepaymentFrequency
    max_repayment_period: Optional[int] = None

    requires_guarantor: bool = False
    is_multiple_of_savings: bool = False
    savings_multiplier: Optional[Decimal] = None

    requires_security: bool = False
    security_type: Optional[SecurityType] = None
    security_value: Optional[Decimal] = None
    security_notes: Optional[str] = None

    requires_deposit: bool = False
    deposit_type: Optional[DepositType] = None
    deposit_value: Optional[Decimal] = None

    late_payment_penalty_type: Optional[LatePaymentPenaltyType] = None
    late_payment_penalty_value: Optional[Decimal] = None

    # Approval config
    requires_appraisal: bool = False
    requires_board_approval: bool = False

    # Aging config
    watchful_after_days: Optional[int] = 30
    non_performing_after_days: Optional[int] = 90
    doubtful_after_days: Optional[int] = 180

    # Rescheduling config
    allows_rescheduling: bool = False
    reschedule_fee_type: Optional[LatePaymentPenaltyType] = None
    reschedule_fee_value: Optional[Decimal] = None

    # Offset config
    allows_offset: bool = False
    offset_covers: Optional[OffsetCoverType] = None
    offset_fee_type: Optional[LatePaymentPenaltyType] = None
    offset_fee_value: Optional[Decimal] = None

    # Repayment allocation order
    allocation_order: Optional[str] = "penalty,interest,principal"

    fees: List[LoanProductFeeCreate] = []
    penalties: List[LoanProductPenaltyCreate] = []


class LoanProductRead(BaseModel):
    id: int
    product_code: str
    version_number: int
    product_name: str
    is_active: bool
    effective_date: date
    interest_method: InterestMethod
    interest_rate: Decimal
    interest_period: InterestPeriod
    repayment_frequency: RepaymentFrequency
    max_repayment_period: Optional[int]

    requires_guarantor: bool
    is_multiple_of_savings: bool
    savings_multiplier: Optional[Decimal]

    requires_security: bool
    security_type: Optional[SecurityType]
    security_value: Optional[Decimal]
    security_notes: Optional[str]

    requires_deposit: bool
    deposit_type: Optional[DepositType]
    deposit_value: Optional[Decimal]

    late_payment_penalty_type: Optional[LatePaymentPenaltyType]
    late_payment_penalty_value: Optional[Decimal]

    requires_appraisal: bool
    requires_board_approval: bool

    watchful_after_days: Optional[int]
    non_performing_after_days: Optional[int]
    doubtful_after_days: Optional[int]

    allows_rescheduling: bool
    reschedule_fee_type: Optional[LatePaymentPenaltyType]
    reschedule_fee_value: Optional[Decimal]

    allows_offset: bool
    offset_covers: Optional[OffsetCoverType]
    offset_fee_type: Optional[LatePaymentPenaltyType]
    offset_fee_value: Optional[Decimal]

    created_at: datetime
    updated_at: datetime

    fees: List[LoanProductFeeRead] = []
    penalties: List[LoanProductPenaltyRead] = []

    model_config = {"from_attributes": True}
