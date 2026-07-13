from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.loan_product import LoanProductCreate, LoanProductRead
from app.crud import loan_product as crud

router = APIRouter(prefix="/api/loan-products", tags=["Loan Products"])


@router.get("", response_model=List[LoanProductRead])
def list_products(active_only: bool = False, db: Session = Depends(get_db)):
    return crud.list_products(db, active_only=active_only)


@router.get("/{product_id}", response_model=LoanProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = crud.get_product_by_id(db, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Product not found.")
    return p


@router.post("", response_model=LoanProductRead, status_code=status.HTTP_201_CREATED)
def create_product(data: LoanProductCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_product(db, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{product_code}", response_model=LoanProductRead)
def update_product(product_code: str, data: LoanProductCreate, db: Session = Depends(get_db)):
    try:
        return crud.update_product(db, product_code, data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
