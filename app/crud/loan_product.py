from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.loan_product import LoanProduct, LoanProductFee
from app.schemas.loan_product import LoanProductCreate
from app.crud.audit import log_action


def get_product_by_id(db: Session, product_id: int) -> Optional[LoanProduct]:
    return db.query(LoanProduct).filter(LoanProduct.id == product_id).first()


def get_active_product_by_code(db: Session, product_code: str) -> Optional[LoanProduct]:
    return (
        db.query(LoanProduct)
        .filter(LoanProduct.product_code == product_code, LoanProduct.is_active == True)
        .first()
    )


def list_products(db: Session, active_only: bool = False) -> List[LoanProduct]:
    q = db.query(LoanProduct)
    if active_only:
        q = q.filter(LoanProduct.is_active == True)
    return q.order_by(LoanProduct.product_code, LoanProduct.version_number.desc()).all()


def create_product(db: Session, data: LoanProductCreate) -> LoanProduct:
    """Create version 1 of a new product. product_code must be unique among active products."""
    existing = get_active_product_by_code(db, data.product_code)
    if existing:
        raise ValueError(
            f"Active product with code '{data.product_code}' already exists (id={existing.id}). "
            "Use PUT /{product_code} to create a new version."
        )

    product = LoanProduct(
        **data.model_dump(exclude={"fees", "penalties"}),
        version_number=1,
        is_active=True,
    )
    db.add(product)
    db.flush()  # get product.id

    for fee_data in data.fees:
        db.add(LoanProductFee(loan_product_id=product.id, **fee_data.model_dump()))
        
    from app.models.penalty import LoanProductPenalty
    for penalty_data in data.penalties:
        db.add(LoanProductPenalty(loan_product_id=product.id, **penalty_data.model_dump()))

    log_action(db, "loan_product", product.id, "created", {
        "product_code": product.product_code,
        "version": product.version_number,
        "product_name": product.product_name,
    })

    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_code: str, data: LoanProductCreate) -> LoanProduct:
    """
    Versioning: deactivate the current active version, create a new row with version+1.
    Existing loans retain their FK to the old version.
    """
    old = get_active_product_by_code(db, product_code)
    if not old:
        raise ValueError(f"No active product found with code '{product_code}'.")

    old.is_active = False
    db.flush()

    new_version = old.version_number + 1
    product = LoanProduct(
        **data.model_dump(exclude={"fees", "penalties"}),
        product_code=product_code,  # always same code
        version_number=new_version,
        is_active=True,
    )
    db.add(product)
    db.flush()

    for fee_data in data.fees:
        db.add(LoanProductFee(loan_product_id=product.id, **fee_data.model_dump()))
        
    from app.models.penalty import LoanProductPenalty
    for penalty_data in data.penalties:
        db.add(LoanProductPenalty(loan_product_id=product.id, **penalty_data.model_dump()))

    log_action(db, "loan_product", product.id, "updated", {
        "product_code": product_code,
        "old_version_id": old.id,
        "new_version": new_version,
    })
    log_action(db, "loan_product", old.id, "deactivated", {
        "reason": f"superseded by version {new_version} (id={product.id})"
    })

    db.commit()
    db.refresh(product)
    return product
