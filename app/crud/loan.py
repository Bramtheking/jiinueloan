from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.loan import Loan, LoanStatus
from app.models.member import Member
from app.models.loan_product import LoanProduct
from app.models.ledger import LedgerTransaction
from app.schemas.loan import LoanCreate
from app.engine.validation import (
    MemberSnapshot, ProductSnapshot, LoanApplicationInput, validate_loan_application
)
from app.engine.fees import FeeConfig, compute_fees, compute_security_and_deposit
from app.crud.audit import log_action


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
    Full loan application processing:
    1. Load member + product from DB
    2. Run validation engine
    3. Create loan record
    4. Post ledger entries (disbursement + fees + security + deposit)
    5. Audit log
    """
    # --- 1. Load entities ---
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

    # --- 2. Validation ---
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

    # --- 3. Create loan ---
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
        disbursement_date=data.disbursement_date or data.application_date,
        status=LoanStatus.active,
        outstanding_balance=data.principal_amount,
    )
    db.add(loan)
    db.flush()  # get loan.id

    today = data.disbursement_date or data.application_date

    # --- 4. Ledger entries ---
    # 4a. Loan disbursement — money going OUT of SACCO to member
    db.add(LedgerTransaction(
        account_name="Jiinue Loan Account",
        description=f"Loan disbursement — {loan.loan_number} to {member.name}",
        money_out=data.principal_amount,
        related_loan_id=loan.id,
        transaction_date=today,
    ))

    # 4b. Fees — money coming IN to SACCO
    fee_cfgs = [
        FeeConfig(
            fee_name=f.fee_name,
            fee_type=f.fee_type.value,
            fee_value=f.fee_value,
            affects_principal=f.affects_principal,
            show_in_statement=f.show_in_statement,
            ledger_account_name=f.ledger_account_name,
        )
        for f in product.fees
    ]
    fee_results = compute_fees(data.principal_amount, fee_cfgs)
    for fee in fee_results:
        if fee.amount > 0:
            db.add(LedgerTransaction(
                account_name=fee.ledger_account_name,
                description=f"{fee.fee_name} — {loan.loan_number}",
                money_in=fee.amount,
                related_loan_id=loan.id,
                transaction_date=today,
            ))

    # 4c. Security deposit (if any and computable)
    sec_dep = compute_security_and_deposit(
        principal=data.principal_amount,
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
            related_loan_id=loan.id,
            transaction_date=today,
        ))
    if sec_dep.deposit_amount > 0:
        db.add(LedgerTransaction(
            account_name="Member Deposit General Account",
            description=f"Upfront deposit — {loan.loan_number}",
            money_in=sec_dep.deposit_amount,
            related_loan_id=loan.id,
            transaction_date=today,
        ))

    # --- 5. Audit ---
    log_action(db, "loan", loan.id, "created", {
        "loan_number": loan.loan_number,
        "member": member.name,
        "product_id": product.id,
        "principal": str(data.principal_amount),
    })

    db.commit()
    db.commit()
    db.refresh(loan)
    return loan


def update_loan(db: Session, loan_id: int, data: dict) -> Optional[Loan]:
    loan = get_loan(db, loan_id)
    if not loan:
        return None

    # Allow partial updates
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

    # Hard delete ledger transactions and repayments associated with this loan
    db.query(LedgerTransaction).filter(LedgerTransaction.related_loan_id == loan_id).delete()
    
    from app.models.repayment import Repayment
    db.query(Repayment).filter(Repayment.loan_id == loan_id).delete()

    db.delete(loan)
    log_action(db, "loan", loan_id, "deleted", {"loan_number": loan.loan_number})
    db.commit()
    return True
