from datetime import date
from decimal import Decimal
from typing import List
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus
from app.models.repayment import Repayment
from app.models.ledger import LedgerTransaction
from app.schemas.repayment import RepaymentCreate
from app.engine.interest import calculate_accrued_interest
from app.engine.repayment import allocate_payment
from app.crud.audit import log_action


def list_repayments(db: Session, loan_id: int) -> List[Repayment]:
    return (
        db.query(Repayment)
        .filter(Repayment.loan_id == loan_id)
        .order_by(Repayment.payment_date)
        .all()
    )


def _get_last_payment_date(db: Session, loan_id: int, disbursement_date: date) -> date:
    last = (
        db.query(Repayment)
        .filter(Repayment.loan_id == loan_id)
        .order_by(Repayment.payment_date.desc())
        .first()
    )
    return last.payment_date if last else disbursement_date


def create_repayment(db: Session, loan_id: int, data: RepaymentCreate) -> Repayment:
    """
    Record a manual repayment.
    Steps (per spec §5.3):
    1. Calculate interest accrued since last payment
    2. Compute any outstanding penalty (late payment)
    3. Allocate: penalty → interest → principal
    4. Update outstanding_balance; close loan if balance hits zero
    5. Post to ledger
    6. Audit log
    """
    loan = db.query(Loan).filter(Loan.id == loan_id).first()
    if not loan:
        raise ValueError(f"Loan id={loan_id} not found.")
    if loan.status not in (LoanStatus.active,):
        raise ValueError(f"Loan {loan.loan_number} is {loan.status.value} and cannot accept repayments.")

    product = loan.loan_product
    disbursement_date = loan.disbursement_date or loan.application_date
    last_payment_date = _get_last_payment_date(db, loan_id, disbursement_date)

    # --- 1. Calculate accrued interest ---
    days_elapsed = (data.payment_date - last_payment_date).days
    if days_elapsed < 0:
        raise ValueError("Payment date cannot be before the last payment date.")
    if days_elapsed == 0:
        days_elapsed = 1  # same-day payment: accrue at least 1 day

    interest_due = calculate_accrued_interest(
        current_balance=loan.outstanding_balance,
        rate_pct=product.interest_rate,
        interest_period=product.interest_period.value,
        days_elapsed=days_elapsed,
        interest_method=product.interest_method.value,
    )

    # --- 2. Compute penalty ---
    penalty_due = Decimal("0")
    if (
        product.late_payment_penalty_type is not None
        and product.late_payment_penalty_value is not None
    ):
        if days_elapsed > 30:  # simple rule: > 30 days gap triggers penalty
            if product.late_payment_penalty_type.value == "percentage":
                penalty_due = loan.outstanding_balance * (
                    product.late_payment_penalty_value / Decimal("100")
                )
            else:
                penalty_due = product.late_payment_penalty_value

    # --- 3. Expected installment (for flag) ---
    expected_installment = Decimal("0")
    if product.max_repayment_period and product.max_repayment_period > 0:
        expected_installment = loan.principal_amount / Decimal(product.max_repayment_period)

    # --- 4. Allocate ---
    allocation = allocate_payment(
        amount_paid=data.amount_paid,
        penalty_due=penalty_due,
        interest_due=interest_due,
        outstanding_principal=loan.outstanding_balance,
        expected_installment=expected_installment,
        allocation_order=product.allocation_order or "penalty,interest,principal",
    )

    # --- 5. Record repayment ---
    repayment = Repayment(
        loan_id=loan_id,
        payment_date=data.payment_date,
        amount_paid=allocation.amount_paid,
        amount_to_penalty=allocation.amount_to_penalty,
        amount_to_interest=allocation.amount_to_interest,
        amount_to_principal=allocation.amount_to_principal,
        remaining_balance_after=allocation.remaining_balance_after,
        is_underpaid=allocation.is_underpaid,
        is_overpaid=allocation.is_overpaid,
        notes=data.notes,
    )
    db.add(repayment)
    db.flush()

    # --- 6. Update loan balance ---
    loan.outstanding_balance = allocation.remaining_balance_after
    if loan.outstanding_balance <= Decimal("0"):
        loan.status = LoanStatus.closed
        loan.outstanding_balance = Decimal("0")

    # --- 6b. Mark schedule entries as paid up to the payment date ---
    from app.models.loan_schedule import LoanScheduleEntry
    unpaid_due = (
        db.query(LoanScheduleEntry)
        .filter(
            LoanScheduleEntry.loan_id == loan_id,
            LoanScheduleEntry.is_paid == False,
            LoanScheduleEntry.is_cancelled == False,
            LoanScheduleEntry.due_date <= data.payment_date,
        )
        .order_by(LoanScheduleEntry.due_date)
        .all()
    )
    remaining_to_allocate = allocation.amount_to_principal + allocation.amount_to_interest
    for entry in unpaid_due:
        if remaining_to_allocate >= entry.expected_amount:
            entry.is_paid = True
            entry.amount_actually_paid = entry.expected_amount
            entry.is_missed = False
            remaining_to_allocate -= entry.expected_amount
        elif remaining_to_allocate > 0:
            # partial payment — mark amount but don't mark fully paid
            entry.amount_actually_paid = entry.amount_actually_paid + remaining_to_allocate
            remaining_to_allocate = Decimal("0")
            break

    # --- 7. Ledger ---
    db.add(LedgerTransaction(
        account_name="Jiinue Loan Account",
        description=f"Repayment — {loan.loan_number} ({data.payment_date})",
        money_in=allocation.amount_paid,
        related_loan_id=loan_id,
        transaction_date=data.payment_date,
    ))

    # --- 8. Audit ---
    log_action(db, "repayment", repayment.id, "created", {
        "loan_number": loan.loan_number,
        "amount_paid": str(allocation.amount_paid),
        "to_penalty": str(allocation.amount_to_penalty),
        "to_interest": str(allocation.amount_to_interest),
        "to_principal": str(allocation.amount_to_principal),
        "remaining_balance": str(allocation.remaining_balance_after),
        "is_underpaid": allocation.is_underpaid,
        "is_overpaid": allocation.is_overpaid,
    })

    # --- 9. Update Member Credit Score ---
    from app.crud.scoring import update_member_credit_score
    if loan.member_id:
        update_member_credit_score(db, loan.member_id)

    db.commit()
    db.refresh(repayment)
    return repayment
