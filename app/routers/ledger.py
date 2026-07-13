from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ledger import (
    LedgerTransactionRead,
    ManualTransactionCreate,
    AuditLogRead,
)
from app.crud import ledger as ledger_crud

router = APIRouter(tags=["Ledger & Audit"])


# ---------------------------------------------------------------------------
# Ledger
# ---------------------------------------------------------------------------

@router.get("/api/ledger", response_model=List[LedgerTransactionRead])
def list_ledger(
    account_name: Optional[str] = None,
    loan_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    return ledger_crud.list_transactions(db, account_name=account_name, loan_id=loan_id)


@router.post(
    "/api/ledger/manual",
    response_model=LedgerTransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def manual_transaction(data: ManualTransactionCreate, db: Session = Depends(get_db)):
    try:
        return ledger_crud.create_manual_transaction(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/ledger/{transaction_id}/reverse", response_model=LedgerTransactionRead)
def reverse_transaction(transaction_id: int, db: Session = Depends(get_db)):
    try:
        return ledger_crud.reverse_transaction(db, transaction_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

@router.get("/api/audit-log", response_model=List[AuditLogRead])
def list_audit_log(
    entity_type: Optional[str] = None, db: Session = Depends(get_db)
):
    return ledger_crud.list_audit_log(db, entity_type=entity_type)
