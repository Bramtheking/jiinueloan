"""
Offset logic.
"""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus
from app.models.ledger import LedgerTransaction
from app.models.loan_product import OffsetCoverType, LatePaymentPenaltyType
from app.crud.loan_schedule import cancel_schedule
from app.crud.audit import log_action
from app.services import sms


def offset_loan(db: Session, loan_id: int, offset_date: date) -> Loan:
    """
    Early payoff / offset using member's savings or security.
    """
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise ValueError("Loan not found")
        
    product = loan.loan_product
    if not product.allows_offset:
        raise ValueError("This loan product does not allow early offset.")
        
    if loan.status not in (LoanStatus.active, LoanStatus.watchful, LoanStatus.non_performing, LoanStatus.doubtful):
        raise ValueError(f"Cannot offset loan in status: {loan.status.value}")
        
    balance = loan.outstanding_balance
    if balance <= 0:
        raise ValueError("Loan is already fully paid off.")
        
    # Check what covers the offset (Savings, Security, or Both)
    # We would normally check if the Member has enough Savings or Security value here.
    # For now, we assume the offset is funded by an internal transfer from the specified cover.
    cover = product.offset_covers
    if not cover:
        raise ValueError("Offset cover not configured on product.")
        
    # Compute offset fee
    fee_charged = Decimal("0")
    if product.offset_fee_value:
        if product.offset_fee_type == LatePaymentPenaltyType.percentage:
            fee_charged = (balance * product.offset_fee_value / Decimal("100")).quantize(Decimal("0.01"))
        else:
            fee_charged = product.offset_fee_value
            
        if fee_charged > 0:
            db.add(LedgerTransaction(
                account_name="Offset Fee Income",
                description=f"Offset fee — {loan.loan_number}",
                money_in=fee_charged,
                related_loan_id=loan.id,
                transaction_date=offset_date,
            ))
            
    total_due = balance + fee_charged
    
    # Post the offset payment
    # Deducting from member savings/security (in a real system we'd deduct from their actual savings balance)
    account_source = "Member Savings" if cover == OffsetCoverType.savings else "Member Security"
    
    # Internal transfer from member source to loan account
    db.add(LedgerTransaction(
        account_name=account_source,
        description=f"Loan Offset Transfer — {loan.loan_number}",
        money_out=total_due,
        transaction_date=offset_date,
    ))
    
    db.add(LedgerTransaction(
        account_name="Principal Receipts",
        description=f"Loan Offset Repayment — {loan.loan_number}",
        money_in=balance,
        related_loan_id=loan.id,
        transaction_date=offset_date,
    ))
    
    # Update Loan status
    loan.outstanding_balance = Decimal("0")
    loan.status = LoanStatus.closed
    loan.days_overdue = 0
    
    # Cancel any remaining unpaid schedule entries
    cancel_schedule(db, loan.id)
    
    log_action(db, "loan", loan.id, "offset", {
        "amount": str(balance),
        "fee": str(fee_charged),
        "source": cover.value,
    })
    
    db.commit()
    db.refresh(loan)
    
    sms.sms_loan_cleared(loan.member.phone, loan.member.name, loan.loan_number)
    return loan
