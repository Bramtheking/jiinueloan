from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.member import Member
from app.schemas.loan import MemberRead
from app.schemas.member import MemberCreate, MemberUpdate

router = APIRouter(prefix="/api/members", tags=["Members"])


@router.get("", response_model=List[MemberRead])
def list_members(db: Session = Depends(get_db)):
    return db.query(Member).order_by(Member.id).all()

@router.get("/{member_id}", response_model=MemberRead)
def get_member(member_id: int, db: Session = Depends(get_db)):
    member = db.query(Member).filter(Member.id == member_id).first()
    if not member:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@router.post("", response_model=MemberRead)
def create_member(data: MemberCreate, db: Session = Depends(get_db)):
    from app.crud import member as member_crud
    return member_crud.create_member(db, name=data.name, phone=data.phone, savings_balance=data.savings_balance)

@router.put("/{member_id}", response_model=MemberRead)
def update_member(member_id: int, data: MemberUpdate, db: Session = Depends(get_db)):
    from app.crud import member as member_crud
    from fastapi import HTTPException
    member = member_crud.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    name = data.name if data.name is not None else member.name
    phone = data.phone if data.phone is not None else member.phone
    savings_balance = data.savings_balance if data.savings_balance is not None else member.savings_balance
    
    return member_crud.update_member(db, member_id, name=name, phone=phone, savings_balance=savings_balance)

@router.delete("/{member_id}", status_code=204)
def delete_member(member_id: int, db: Session = Depends(get_db)):
    from app.crud import member as member_crud
    from fastapi import HTTPException
    success = member_crud.delete_member(db, member_id)
    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return None
