"""
MemberCreditScore — one row per member, updated on every repayment and aging run.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MemberCreditScore(Base):
    __tablename__ = "member_credit_scores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    member_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("members.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )

    score: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    label: Mapped[str] = mapped_column(String(20), nullable=False, default="Fair")

    # Raw counts used for calculation (cumulative across all loans)
    on_time_payments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    underpayments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    missed_payments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    loans_closed_on_time: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    member: Mapped["Member"] = relationship("Member", back_populates="credit_score")  # type: ignore[name-defined]
