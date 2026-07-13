from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel

from app.models.loan import LoanStatus


class MemberRead(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    savings_balance: Decimal
    created_at: datetime

    class Config:
        orm_mode = True


class LoanCreate(BaseModel):
    member_id: int
    loan_product_id: int
    guarantor_member_id: Optional[int] = None
    principal_amount: Decimal
    application_date: date
    disbursement_date: Optional[date] = None

    security_provided_value: Optional[Decimal] = None
    security_provided_notes: Optional[str] = None
    deposit_paid_amount: Optional[Decimal] = None


class LoanRead(BaseModel):
    id: int
    loan_number: str
    member_id: int
    loan_product_id: int
    guarantor_member_id: Optional[int]
    principal_amount: Decimal
    security_provided_value: Optional[Decimal]
    security_provided_notes: Optional[str]
    deposit_paid_amount: Optional[Decimal]
    application_date: date
    disbursement_date: Optional[date]
    status: LoanStatus
    outstanding_balance: Decimal
    created_at: datetime

    class Config:
        orm_mode = True


class LoanUpdate(BaseModel):
    status: Optional[LoanStatus] = None
    outstanding_balance: Optional[Decimal] = None
    guarantor_member_id: Optional[int] = None
    security_provided_value: Optional[Decimal] = None
    security_provided_notes: Optional[str] = None
    deposit_paid_amount: Optional[Decimal] = None
