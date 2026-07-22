from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class MemberDeposit(Base):
    """
    Member deposits — cash held by the SACCO as security or savings.
    Separate from loan deposits (which are tied to a specific loan).
    """
    __tablename__ = "member_deposits"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    deposit_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_locked: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)  # locked if used as loan security
    related_loan_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("loans.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    member: Mapped["Member"] = relationship("Member", back_populates="deposits")  # type: ignore
    related_loan: Mapped["Loan | None"] = relationship("Loan")  # type: ignore
