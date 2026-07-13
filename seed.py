"""
seed.py — Populates the members table with sample data.

Run with:
    .venv\\Scripts\\python seed.py
    (or: python seed.py  if .venv is activated)
"""

from decimal import Decimal
from sqlalchemy.orm import Session

from app.database import engine, SessionLocal
from app.models.member import Member


SAMPLE_MEMBERS = [
    {"name": "Alice Wanjiku",   "phone": "0712 345 678", "savings_balance": Decimal("150000.00")},
    {"name": "Brian Otieno",    "phone": "0723 456 789", "savings_balance": Decimal("45000.00")},
    {"name": "Catherine Njeri", "phone": "0734 567 890", "savings_balance": Decimal("320000.00")},
    {"name": "David Kamau",     "phone": "0745 678 901", "savings_balance": Decimal("8000.00")},
    {"name": "Esther Achieng",  "phone": "0756 789 012", "savings_balance": Decimal("210000.00")},
    {"name": "Francis Mwangi",  "phone": "0767 890 123", "savings_balance": Decimal("60000.00")},
    {"name": "Grace Chebet",    "phone": "0778 901 234", "savings_balance": Decimal("95000.00")},
    {"name": "Hassan Omar",     "phone": "0789 012 345", "savings_balance": Decimal("0.00")},
    {"name": "Irene Mutua",     "phone": "0790 123 456", "savings_balance": Decimal("500000.00")},
    {"name": "James Kariuki",   "phone": "0701 234 567", "savings_balance": Decimal("33000.00")},
]


def seed(db: Session) -> None:
    existing = db.query(Member).count()
    if existing > 0:
        print(f"[seed] Members table already has {existing} rows — skipping.")
        return

    members = [Member(**m) for m in SAMPLE_MEMBERS]
    db.add_all(members)
    db.commit()
    print(f"[seed] Inserted {len(members)} sample members.")
    for m in members:
        db.refresh(m)
        print(f"  #{m.id:>2} {m.name:<20} savings: KES {m.savings_balance:>12,.2f}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
