"""
CRUD operations for Loan Schedule.
"""

from decimal import Decimal
from typing import List

from sqlalchemy.orm import Session

from app.models.loan_schedule import LoanScheduleEntry


def create_schedule_entries(db: Session, entries: List[LoanScheduleEntry]):
    """Bulk create schedule entries."""
    db.add_all(entries)
    db.flush()


def get_schedule(db: Session, loan_id: int) -> List[LoanScheduleEntry]:
    """Get the full schedule for a loan."""
    return (
        db.query(LoanScheduleEntry)
        .filter(LoanScheduleEntry.loan_id == loan_id)
        .order_by(LoanScheduleEntry.period_number)
        .all()
    )


def cancel_schedule(db: Session, loan_id: int):
    """Mark all unpaid schedule entries as cancelled (used during rescheduling)."""
    db.query(LoanScheduleEntry).filter(
        LoanScheduleEntry.loan_id == loan_id,
        LoanScheduleEntry.is_paid == False,
    ).update({"is_cancelled": True})
    db.flush()
