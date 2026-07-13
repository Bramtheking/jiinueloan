from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus
from app.models.member import Member
from app.models.loan_product import LoanProduct
from app.models.ledger import LedgerTransaction
from app.models.loan_schedule import LoanScheduleEntry
from app.schemas.loan import LoanCreate
from app.engine.validation import (
    MemberSnapshot, ProductSnapshot, LoanApplicationInput, validate_loan_application
)
from app.engine.fees import FeeConfig, compute_fees, compute_security_and_deposit
from app.engine.schedule import generate_schedule
from app.crud.audit import log_action
from app.services import sms


def _generate_loan_number(db: Session) -> str:
    today = date.today().strftime("%Y%m%d")
    count = db.query(Loan).filter(Loan.loan_number.like(f"LN-{today}-%")).count()
    return f"LN-{today}-{(count + 1):05d}"


def get_loan(db: Session, loan_id: int) -> Optional[Loan]:
    return db.query(Loan).filter(Loan.id == loan_id).first()


def list_loans(db: Session) -> List[Loan]:
    return db.query(Loan).order_by(Loan.id.desc()).all()


def create_loan(db: Session, data: LoanCreate) -> Loan:
    """
    Step 1 of loan lifecycle: Application.
    Creates loan in pending_application status. No ledger entries yet.
    """
    member = db.query(Member).filter(Member.id == data.member_id).first()
    if not member:
        raise ValueError(f"Member id={data.member_id} not found.")

    product = db.query(LoanProduct).filter(LoanProduct.id == data.loan_product_id).first()
    if not product:
        raise ValueError(f"Loan product id={data.loan_product_id} not found.")
    if not product.is_active:
        raise ValueError(
            f"Loan product id={data.loan_product_id} is not active. "
            "Select the current active version."
        )

    member_snap = MemberSnapshot(
        id=member.id, name=member.name, savings_balance=member.savings_balance
    )
    product_snap = ProductSnapshot(
        is_multiple_of_savings=product.is_multiple_of_savings,
        savings_multiplier=product.savings_multiplier,
        requires_guarantor=product.requires_guarantor,
        requires_security=product.requires_security,
        security_type=product.security_type.value if product.security_type else None,
        security_value=product.security_value,
        requires_deposit=product.requires_deposit,
        deposit_type=product.deposit_type.value if product.deposit_type else None,
        deposit_value=product.deposit_value,
    )
    inp = LoanApplicationInput(
        member=member_snap,
        product=product_snap,
        requested_principal=data.principal_amount,
        guarantor_id=data.guarantor_member_id,
        security_value_provided=data.security_provided_value,
        security_notes_provided=data.security_provided_notes,
        deposit_amount_provided=data.deposit_paid_amount,
    )
    validation = validate_loan_application(inp)
    if not validation.is_valid:
        raise ValueError("Loan application validation failed: " + "; ".join(validation.errors))

    # Fast-track statuses if no approval required
    initial_status = LoanStatus.pending_application
    if not product.requires_appraisal and not product.requires_board_approval:
        initial_status = LoanStatus.approved

    loan = Loan(
        loan_number=_generate_loan_number(db),
        member_id=data.member_id,
        loan_product_id=data.loan_product_id,
        guarantor_member_id=data.guarantor_member_id,
        principal_amount=data.principal_amount,
        security_provided_value=data.security_provided_value,
        security_provided_notes=data.security_provided_notes,
        deposit_paid_amount=data.deposit_paid_amount,
        application_date=data.application_date,
        disbursement_date=data.disbursement_date,
        num_periods=data.num_periods or product.max_repayment_period or 12,
        status=initial_status,
        outstanding_balance=data.principal_amount,
    )
    db.add(loan)
    db.flush()

    log_action(db, "loan", loan.id, "created", {
        "loan_number": loan.loan_number,
        "member": member.name,
        "product_id": product.id,
        "principal": str(data.principal_amount),
        "status": initial_status.value,
    })

    db.commit()
    db.refresh(loan)

    sms.sms_loan_applied(member.phone, member.name, loan.loan_number, str(loan.principal_amount))
    return loan


def approve_loan(db: Session, loan_id: int, notes: str | None = None) -> Loan:
    loan = get_loan(db, loan_id)
    if not loan:
        raise ValueError("Loan not found")
    
    if loan.status == LoanStatus.pending_application:
        if loan.loan_product.requires_board_approval:
            loan.status = LoanStatus.appraised
        else:
            loan.status = LoanStatus.approved
    elif loan.status == LoanStatus.appraised:
        loan.status = LoanStatus.approved
    else:
        raise ValueError(f"Cannot approve loan in status: {loan.status.value}")

    if notes:
        if loan.status == LoanStatus.appraised:
            loan.appraisal_notes = notes
        else:
            loan.approval_notes = notes

    log_action(db, "loan", loan.id, "approved", {"new_status": loan.status.value})
    db.commit()
    db.refresh(loan)
    
    if loan.status == LoanStatus.approved:
        sms.sms_loan_approved(loan.member.phone, loan.member.name, loan.loan_number)

    return loan


def reject_loan(db: Session, loan_id: int, reason: str) -> Loan:
    loan = get_loan(db, loan_id)
    if not loan:
        raise ValueError("Loan not found")
    
    if loan.status not in (LoanStatus.pending_application, LoanStatus.appraised):
        raise ValueError("Can only reject pending or appraised loans.")

    loan.status = LoanStatus.rejected
    loan.rejection_reason = reason

    log_action(db, "loan", loan.id, "rejected", {"reason": reason})
    db.commit()
    db.refresh(loan)
    
    sms.sms_loan_rejected(loan.member.phone, loan.member.name, loan.loan_number, reason)
    return loan


def disburse_loan(db: Session, loan_id: int, disburse_date: date) -> Loan:
    loan = get_loan(db, loan_id)
    if not loan:
        raise ValueError("Loan not found")

    if loan.status != LoanStatus.approved:
        raise ValueError("Loan must be approved before disbursement.")

    loan.status = LoanStatus.active
    loan.disbursement_date = disburse_date
    product = loan.loan_product
    member = loan.member

    # --- 1. Ledger Entries ---
    db.add(LedgerTransaction(
        account_name="Jiinue Loan Account",
        description=f"Loan disbursement — {loan.loan_number} to {member.name}",
        money_out=loan.principal_amount,
        related_loan_id=loan.id,
        transaction_date=disburse_date,
    ))

    fee_cfgs = [
        FeeConfig(
            fee_name=f.fee_name, fee_type=f.fee_type.value, fee_value=f.fee_value,
            affects_principal=f.affects_principal, show_in_statement=f.show_in_statement,
            ledger_account_name=f.ledger_account_name,
        ) for f in product.fees
    ]
    for fee in compute_fees(loan.principal_amount, fee_cfgs):
        if fee.amount > 0:
            db.add(LedgerTransaction(
                account_name=fee.ledger_account_name,
                description=f"{fee.fee_name} — {loan.loan_number}",
                money_in=fee.amount,
                related_loan_id=loan.id,
                transaction_date=disburse_date,
            ))

    sec_dep = compute_security_and_deposit(
        principal=loan.principal_amount,
        requires_security=product.requires_security,
        security_type=product.security_type.value if product.security_type else None,
        security_value=product.security_value,
        requires_deposit=product.requires_deposit,
        deposit_type=product.deposit_type.value if product.deposit_type else None,
        deposit_value=product.deposit_value,
    )
    if sec_dep.security_amount > 0:
        db.add(LedgerTransaction(
            account_name="Member Deposit General Account",
            description=f"Security deposit — {loan.loan_number}",
            money_in=sec_dep.security_amount,
            related_loan_id=loan.id, transaction_date=disburse_date,
        ))
    if sec_dep.deposit_amount > 0:
        db.add(LedgerTransaction(
            account_name="Member Deposit General Account",
            description=f"Upfront deposit — {loan.loan_number}",
            money_in=sec_dep.deposit_amount,
            related_loan_id=loan.id, transaction_date=disburse_date,
        ))

    # --- 2. Generate Repayment Schedule ---
    sched = generate_schedule(
        principal=loan.principal_amount,
        interest_rate_pct=product.interest_rate,
        interest_period=product.interest_period.value,
        interest_method=product.interest_method.value,
        repayment_frequency=product.repayment_frequency.value,
        num_periods=loan.num_periods or 12,
        disbursement_date=disburse_date,
    )
    for s in sched:
        db.add(LoanScheduleEntry(
            loan_id=loan.id,
            period_number=s.period_number,
            due_date=s.due_date,
            expected_amount=s.expected_amount,
            expected_principal=s.expected_principal,
            expected_interest=s.expected_interest,
            opening_balance=s.opening_balance,
            closing_balance=s.closing_balance,
        ))

    log_action(db, "loan", loan.id, "disbursed", {"date": str(disburse_date)})
    db.commit()
    db.refresh(loan)
    
    sms.sms_loan_disbursed(member.phone, member.name, loan.loan_number, str(loan.principal_amount))
    return loan


def update_loan(db: Session, loan_id: int, data: dict) -> Optional[Loan]:
    loan = get_loan(db, loan_id)
    if not loan:
        return None

    for key, value in data.items():
        if hasattr(loan, key):
            setattr(loan, key, value)

    log_action(db, "loan", loan.id, "updated", data)
    db.commit()
    db.refresh(loan)
    return loan


def delete_loan(db: Session, loan_id: int) -> bool:
    loan = get_loan(db, loan_id)
    if not loan:
        return False

    db.query(LedgerTransaction).filter(LedgerTransaction.related_loan_id == loan_id).delete()
    db.query(LoanScheduleEntry).filter(LoanScheduleEntry.loan_id == loan_id).delete()
    
    from app.models.repayment import Repayment
    db.query(Repayment).filter(Repayment.loan_id == loan_id).delete()

    db.delete(loan)
    log_action(db, "loan", loan_id, "deleted", {"loan_number": loan.loan_number})
    db.commit()
    return True
