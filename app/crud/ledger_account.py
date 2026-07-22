from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.ledger_account import LedgerAccount


def list_accounts(db: Session, active_only: bool = False) -> List[LedgerAccount]:
    q = db.query(LedgerAccount)
    if active_only:
        q = q.filter(LedgerAccount.is_active == True)
    return q.order_by(LedgerAccount.name).all()


def get_account(db: Session, account_id: int) -> Optional[LedgerAccount]:
    return db.query(LedgerAccount).filter(LedgerAccount.id == account_id).first()


def create_account(db: Session, name: str, description: str = "", account_type: str = "") -> LedgerAccount:
    existing = db.query(LedgerAccount).filter(LedgerAccount.name == name).first()
    if existing:
        raise ValueError(f"Ledger account '{name}' already exists.")
    acc = LedgerAccount(
        name=name.strip(),
        description=description.strip() or None,
        account_type=account_type.strip() or None,
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    return acc


def update_account(db: Session, account_id: int, name: str, description: str = "", account_type: str = "", is_active: bool = True) -> LedgerAccount:
    acc = get_account(db, account_id)
    if not acc:
        raise ValueError("Account not found.")
    acc.name = name.strip()
    acc.description = description.strip() or None
    acc.account_type = account_type.strip() or None
    acc.is_active = is_active
    db.commit()
    db.refresh(acc)
    return acc


def delete_account(db: Session, account_id: int) -> bool:
    acc = get_account(db, account_id)
    if not acc:
        return False
    db.delete(acc)
    db.commit()
    return True


def get_account_names(db: Session) -> List[str]:
    return [a.name for a in list_accounts(db, active_only=True)]
