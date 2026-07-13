from decimal import Decimal
from typing import Optional
from pydantic import BaseModel

class MemberCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    savings_balance: Decimal = Decimal("0.00")

class MemberUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    savings_balance: Optional[Decimal] = None
