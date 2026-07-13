from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Member(Base):
    """
    SACCO member. Owns the loan application — other modules handle KYC/registration.
    """

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    savings_balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0.00")
    )

    # Blacklisted members cannot apply for new loans
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    blacklist_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationship to credit score (one-to-one)
    credit_score: Mapped["MemberCreditScore | None"] = relationship(  # type: ignore[name-defined]
        "MemberCreditScore", back_populates="member", uselist=False
    )
