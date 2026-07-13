from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Member(Base):
    """
    Stub/seed table for SACCO members.
    This module does NOT own member registration or KYC — those are handled
    by a separate module.  Only the fields needed for loan validation are here.
    """

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Read-only from this module's perspective; set/updated by the savings module.
    savings_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
