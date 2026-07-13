from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class LedgerTransactionRead(BaseModel):
    id: int
    account_name: str
    description: str
    money_in: Optional[Decimal]
    money_out: Optional[Decimal]
    related_loan_id: Optional[int]
    transaction_date: date
    is_reversed: bool
    reversal_of_transaction_id: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


class ManualTransactionCreate(BaseModel):
    account_name: str
    description: str
    money_in: Optional[Decimal] = None
    money_out: Optional[Decimal] = None
    related_loan_id: Optional[int] = None
    transaction_date: date


class AuditLogRead(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    details: Optional[str]
    timestamp: datetime

    model_config = {"from_attributes": True}
