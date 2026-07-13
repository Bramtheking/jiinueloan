from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.loan import LoanCreate, LoanRead, LoanUpdate
from app.schemas.repayment import RepaymentCreate, RepaymentRead
from app.crud import loan as loan_crud
from app.crud import repayment as repayment_crud

router = APIRouter(prefix="/api/loans", tags=["Loans"])


@router.get("", response_model=List[LoanRead])
def list_loans(db: Session = Depends(get_db)):
    return loan_crud.list_loans(db)


@router.get("/{loan_id}", response_model=LoanRead)
def get_loan(loan_id: int, db: Session = Depends(get_db)):
    loan = loan_crud.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found.")
    return loan


@router.post("", response_model=LoanRead, status_code=status.HTTP_201_CREATED)
def apply_loan(data: LoanCreate, db: Session = Depends(get_db)):
    try:
        return loan_crud.create_loan(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{loan_id}/repayments", response_model=List[RepaymentRead])
def list_repayments(loan_id: int, db: Session = Depends(get_db)):
    return repayment_crud.list_repayments(db, loan_id)


@router.post(
    "/{loan_id}/repayments",
    response_model=RepaymentRead,
    status_code=status.HTTP_201_CREATED,
)
def record_repayment(
    loan_id: int, data: RepaymentCreate, db: Session = Depends(get_db)
):
    try:
        return repayment_crud.create_repayment(db, loan_id, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{loan_id}", response_model=LoanRead)
def update_loan(loan_id: int, data: LoanUpdate, db: Session = Depends(get_db)):
    loan = loan_crud.update_loan(db, loan_id, data.model_dump(exclude_unset=True))
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found.")
    return loan

@router.delete("/{loan_id}", status_code=204)
def delete_loan(loan_id: int, db: Session = Depends(get_db)):
    success = loan_crud.delete_loan(db, loan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Loan not found.")
    return None
