from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class RepaymentCreate(BaseModel):
    payment_date: date
    amount_paid: Decimal
    notes: Optional[str] = None


class RepaymentRead(BaseModel):
    id: int
    loan_id: int
    payment_date: date
    amount_paid: Decimal
    amount_to_penalty: Decimal
    amount_to_interest: Decimal
    amount_to_principal: Decimal
    remaining_balance_after: Decimal
    is_underpaid: bool
    is_overpaid: bool
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
