from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class LoanGuarantor(Base):
    """Many-to-many between loans and guarantor members."""
    __tablename__ = "loan_guarantors"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    loan_id: Mapped[int] = mapped_column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False, index=True)
    member_id: Mapped[int] = mapped_column(Integer, ForeignKey("members.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    loan: Mapped["Loan"] = relationship("Loan", back_populates="guarantors")  # type: ignore
    member: Mapped["Member"] = relationship("Member")  # type: ignore
