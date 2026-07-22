from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Asset(Base):
    """
    Asset register — physical or financial assets owned by members
    that can be used as collateral for loan offsetting.
    """
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id"), nullable=False, index=True)
    asset_name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Land", "Vehicle", "Equipment"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_value: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    valuation_date: Mapped[date] = mapped_column(Date, nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Title deed, log book, etc.
    is_pledged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # locked as collateral
    pledged_loan_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("loans.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    member: Mapped["Member"] = relationship("Member", back_populates="assets")  # type: ignore
    pledged_loan: Mapped["Loan | None"] = relationship("Loan")  # type: ignore
