from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, validator

from app.models.loan_product import (
    InterestMethod,
    InterestPeriod,
    RepaymentFrequency,
    SecurityType,
    FeeType,
    DepositType,
    LatePaymentPenaltyType,
)


# ---------------------------------------------------------------------------
# Loan Product Fee Schemas
# ---------------------------------------------------------------------------

class LoanProductFeeCreate(BaseModel):
    fee_name: str
    fee_type: FeeType
    fee_value: Decimal
    affects_principal: bool = False
    show_in_statement: bool = True
    ledger_account_name: str


class LoanProductFeeRead(LoanProductFeeCreate):
    id: int
    loan_product_id: int

    class Config:
        orm_mode = True


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

    fees: List[LoanProductFeeCreate] = []


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

    created_at: datetime
    updated_at: datetime

    fees: List[LoanProductFeeRead] = []

    class Config:
        orm_mode = True
