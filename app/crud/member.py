from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.member import Member

def create_member(db: Session, name: str, phone: str = None, savings_balance: Decimal = Decimal("0.00")):
    member = Member(name=name, phone=phone, savings_balance=savings_balance)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

def get_member(db: Session, member_id: int):
    return db.query(Member).filter(Member.id == member_id).first()

def update_member(db: Session, member_id: int, name: str, phone: str, savings_balance: Decimal):
    member = get_member(db, member_id)
    if member:
        member.name = name
        member.phone = phone
        member.savings_balance = savings_balance
        db.commit()
        db.refresh(member)
    return member

def delete_member(db: Session, member_id: int):
    member = get_member(db, member_id)
    if member:
        db.delete(member)
        db.commit()
        return True
    return False
