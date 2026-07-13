"""
Reschedule logic.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus
from app.models.loan_reschedule import LoanReschedule
from app.models.loan_schedule import LoanScheduleEntry
from app.models.ledger import LedgerTransaction
from app.models.loan_product import LatePaymentPenaltyType
from app.crud.loan_schedule import cancel_schedule
from app.crud.audit import log_action
from app.engine.schedule import generate_schedule
from app.services import sms


def reschedule_loan(db: Session, loan_id: int, new_num_periods: int, reason: str, reschedule_date: date) -> Loan:
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise ValueError("Loan not found")
        
    product = loan.loan_product
    if not product.allows_rescheduling:
        raise ValueError("This loan product does not allow rescheduling.")
        
    if loan.status not in (LoanStatus.active, LoanStatus.watchful, LoanStatus.non_performing):
        raise ValueError(f"Cannot reschedule loan in status: {loan.status.value}")
        
    if new_num_periods <= 0:
        raise ValueError("New number of periods must be > 0.")
        
    old_num_periods = loan.num_periods or 12
    old_balance = loan.outstanding_balance
    
    # 1. Cancel remaining unpaid schedule entries
    cancel_schedule(db, loan.id)
    
    # 2. Compute reschedule fee
    fee_charged = Decimal("0")
    if product.reschedule_fee_value:
        if product.reschedule_fee_type == LatePaymentPenaltyType.percentage:
            fee_charged = (old_balance * product.reschedule_fee_value / Decimal("100")).quantize(Decimal("0.01"))
        else:
            fee_charged = product.reschedule_fee_value
            
        if fee_charged > 0:
            db.add(LedgerTransaction(
                account_name="Rescheduling Fee Income",
                description=f"Reschedule fee — {loan.loan_number}",
                money_in=fee_charged,
                related_loan_id=loan.id,
                transaction_date=reschedule_date,
            ))
            # The fee doesn't increase outstanding balance unless configured to affect principal.
            # For simplicity, fee is posted to ledger and expected to be paid out of pocket or from savings,
            # or it can be added to outstanding balance. Here we add to outstanding balance.
            loan.outstanding_balance += fee_charged
            
    # 3. Generate new schedule starting from today for the remaining balance
    sched = generate_schedule(
        principal=loan.outstanding_balance,
        interest_rate_pct=product.interest_rate,
        interest_period=product.interest_period.value,
        interest_method=product.interest_method.value,
        repayment_frequency=product.repayment_frequency.value,
        num_periods=new_num_periods,
        disbursement_date=reschedule_date,
    )
    
    # Find max existing period number to continue numbering
    max_period = db.query(LoanScheduleEntry).filter(LoanScheduleEntry.loan_id == loan.id).order_by(LoanScheduleEntry.period_number.desc()).first()
    start_period = (max_period.period_number if max_period else 0) + 1
    
    for s in sched:
        db.add(LoanScheduleEntry(
            loan_id=loan.id,
            period_number=start_period + s.period_number - 1,
            due_date=s.due_date,
            expected_amount=s.expected_amount,
            expected_principal=s.expected_principal,
            expected_interest=s.expected_interest,
            opening_balance=s.opening_balance,
            closing_balance=s.closing_balance,
        ))
        
    new_installment = sched[0].expected_amount if sched else Decimal("0")
        
    # 4. Record reschedule event
    reschedule = LoanReschedule(
        loan_id=loan.id,
        reschedule_date=reschedule_date,
        reason=reason,
        old_num_periods=old_num_periods,
        old_outstanding_balance=old_balance,
        new_num_periods=new_num_periods,
        new_installment=new_installment,
        fee_charged=fee_charged,
    )
    db.add(reschedule)
    
    loan.num_periods = new_num_periods
    loan.status = LoanStatus.active  # restore to active
    loan.days_overdue = 0
    
    log_action(db, "loan", loan.id, "rescheduled", {
        "reason": reason,
        "old_balance": str(old_balance),
        "new_balance": str(loan.outstanding_balance),
        "fee": str(fee_charged),
    })
    
    db.commit()
    db.refresh(loan)
    
    sms.sms_loan_rescheduled(loan.member.phone, loan.member.name, loan.loan_number, str(new_installment))
    return loan
