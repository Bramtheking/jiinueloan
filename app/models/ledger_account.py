from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class LedgerAccount(Base):
    """
    Chart of accounts — a simple named list of ledger accounts.
    Transactions reference account_name; this table is the master list.
    """
    __tablename__ = "ledger_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    account_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # e.g. loan_disbursement, interest_income, fee_income, penalty_income, member_deposit, savings, expense, other
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
