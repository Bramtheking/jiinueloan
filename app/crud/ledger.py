from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.ledger import LedgerTransaction
from app.models.audit_log import AuditLog
from app.schemas.ledger import ManualTransactionCreate
from app.crud.audit import log_action


def list_transactions(
    db: Session,
    account_name: Optional[str] = None,
    loan_id: Optional[int] = None,
) -> List[LedgerTransaction]:
    q = db.query(LedgerTransaction)
    if account_name:
        q = q.filter(LedgerTransaction.account_name.ilike(f"%{account_name}%"))
    if loan_id:
        q = q.filter(LedgerTransaction.related_loan_id == loan_id)
    return q.order_by(LedgerTransaction.transaction_date.desc(), LedgerTransaction.id.desc()).all()


def create_manual_transaction(
    db: Session, data: ManualTransactionCreate
) -> LedgerTransaction:
    txn = LedgerTransaction(
        account_name=data.account_name,
        description=data.description,
        money_in=data.money_in,
        money_out=data.money_out,
        related_loan_id=data.related_loan_id,
        transaction_date=data.transaction_date,
    )
    db.add(txn)
    db.flush()

    log_action(db, "ledger_transaction", txn.id, "created", {
        "account": data.account_name,
        "money_in": str(data.money_in),
        "money_out": str(data.money_out),
        "manual": True,
    })
    db.commit()
    db.refresh(txn)
    return txn


def reverse_transaction(db: Session, transaction_id: int) -> LedgerTransaction:
    """
    Reverse a ledger transaction:
    - Mark the original as is_reversed=True
    - Create a new offsetting row pointing back to the original
    """
    original = db.query(LedgerTransaction).filter(LedgerTransaction.id == transaction_id).first()
    if not original:
        raise ValueError(f"Ledger transaction id={transaction_id} not found.")
    if original.is_reversed:
        raise ValueError(f"Transaction id={transaction_id} has already been reversed.")

    original.is_reversed = True

    offset = LedgerTransaction(
        account_name=original.account_name,
        description=f"REVERSAL of txn #{transaction_id}: {original.description}",
        money_in=original.money_out,   # swap in/out
        money_out=original.money_in,
        related_loan_id=original.related_loan_id,
        transaction_date=original.transaction_date,
        reversal_of_transaction_id=original.id,
    )
    db.add(offset)
    db.flush()

    log_action(db, "ledger_transaction", original.id, "reversed", {
        "offset_transaction_id": offset.id,
    })
    log_action(db, "ledger_transaction", offset.id, "created", {
        "type": "reversal",
        "reversal_of": original.id,
    })

    db.commit()
    db.refresh(offset)
    return offset


def list_audit_log(db: Session, entity_type: Optional[str] = None) -> List[AuditLog]:
    q = db.query(AuditLog)
    if entity_type:
        q = q.filter(AuditLog.entity_type == entity_type)
    return q.order_by(AuditLog.timestamp.desc()).all()
