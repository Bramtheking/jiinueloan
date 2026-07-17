"""
Jiinue Loan Engine — FastAPI application entry point.

Mounts:
  /api/*          → JSON API (all routers)
  /               → Jinja2 admin UI routes
  /static         → CSS / static assets
"""

import os
from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
from datetime import date

from app.database import get_db, engine
from app.models import (
    Member, LoanProduct, Loan, Repayment, LedgerTransaction, AuditLog
)
# Ensure all tables exist (Alembic is preferred for prod; this is a safety net)
# In production, run: alembic upgrade head
from app.database import Base
# Base.metadata.create_all(bind=engine)  # Uncomment only if not using Alembic

from app.routers import loan_products, members, loans, ledger as ledger_router
from app.crud import loan_product as lp_crud
from app.crud import loan as loan_crud
from app.crud import repayment as repayment_crud
from app.crud import ledger as ledger_crud
from app.crud import member as member_crud
from app.schemas.loan_product import LoanProductCreate, LoanProductFeeCreate
from app.schemas.loan import LoanCreate
from app.schemas.repayment import RepaymentCreate
from app.schemas.ledger import ManualTransactionCreate
from app.models.loan_product import (
    InterestMethod, InterestPeriod, RepaymentFrequency,
    SecurityType, FeeType, DepositType, LatePaymentPenaltyType, OffsetCoverType
)
from app.models.penalty import PenaltyTrigger, PenaltyBasis

from contextlib import asynccontextmanager
from app.services.scheduler import start_scheduler, shutdown_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    shutdown_scheduler()

app = FastAPI(
    title="Jiinue Loan Engine",
    description="SACCO loan management module — loan products, loans, repayments, ledger",
    version="1.0.0",
    lifespan=lifespan,
)

# --- Static files ---
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(_BASE_DIR, "app", "static")), name="static")

# --- Templates ---
templates = Jinja2Templates(directory=os.path.join(_BASE_DIR, "app", "templates"))

# --- API routers ---
app.include_router(loan_products.router)
app.include_router(members.router)
app.include_router(loans.router)
app.include_router(ledger_router.router)


# ===========================================================================
# Admin UI routes
# ===========================================================================

# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    total_loans = db.query(Loan).count()
    active_loans = db.query(Loan).filter(Loan.status == "active").count()
    total_products = db.query(LoanProduct).filter(LoanProduct.is_active == True).count()
    total_members = db.query(Member).count()

    from sqlalchemy import func
    total_disbursed = db.query(func.sum(LedgerTransaction.money_out)).filter(
        LedgerTransaction.account_name == "Jiinue Loan Account",
        LedgerTransaction.is_reversed == False,
    ).scalar() or Decimal("0")

    total_collected = db.query(func.sum(LedgerTransaction.money_in)).filter(
        LedgerTransaction.is_reversed == False,
    ).scalar() or Decimal("0")

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "total_loans": total_loans,
        "active_loans": active_loans,
        "total_products": total_products,
        "total_members": total_members,
        "total_disbursed": total_disbursed,
        "total_collected": total_collected,
    })


# ---------------------------------------------------------------------------
# Loan Products UI
# ---------------------------------------------------------------------------

@app.get("/loan-products", response_class=HTMLResponse)
def ui_list_products(request: Request, db: Session = Depends(get_db)):
    products = lp_crud.list_products(db)
    return templates.TemplateResponse("loan_products/list.html", {
        "request": request,
        "products": products,
    })


@app.get("/loan-products/new", response_class=HTMLResponse)
def ui_new_product_form(request: Request):
    return templates.TemplateResponse("loan_products/form.html", {
        "request": request,
        "product": None,
        "interest_methods": [e.value for e in InterestMethod],
        "interest_periods": [e.value for e in InterestPeriod],
        "repayment_frequencies": [e.value for e in RepaymentFrequency],
        "security_types": [e.value for e in SecurityType],
        "deposit_types": [e.value for e in DepositType],
        "penalty_types": [e.value for e in LatePaymentPenaltyType],
        "fee_types": [e.value for e in FeeType],
        "penalty_triggers": [e.value for e in PenaltyTrigger],
        "penalty_basis": [e.value for e in PenaltyBasis],
        "offset_covers": [e.value for e in OffsetCoverType],
        "error": None,
    })


@app.get("/loan-products/{product_id}/edit", response_class=HTMLResponse)
def ui_edit_product_form(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = lp_crud.get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return templates.TemplateResponse("loan_products/form.html", {
        "request": request,
        "product": product,
        "interest_methods": [e.value for e in InterestMethod],
        "interest_periods": [e.value for e in InterestPeriod],
        "repayment_frequencies": [e.value for e in RepaymentFrequency],
        "security_types": [e.value for e in SecurityType],
        "deposit_types": [e.value for e in DepositType],
        "penalty_types": [e.value for e in LatePaymentPenaltyType],
        "fee_types": [e.value for e in FeeType],
        "penalty_triggers": [e.value for e in PenaltyTrigger],
        "penalty_basis": [e.value for e in PenaltyBasis],
        "offset_covers": [e.value for e in OffsetCoverType],
        "error": None,
    })


@app.post("/loan-products/new")
async def ui_create_product(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        fees = _parse_fees_from_form(form)
        data = LoanProductCreate(
            product_code=form["product_code"],
            product_name=form["product_name"],
            effective_date=form["effective_date"],
            interest_method=form["interest_method"],
            interest_rate=form["interest_rate"],
            interest_period=form["interest_period"],
            repayment_frequency=form["repayment_frequency"],
            max_repayment_period=form.get("max_repayment_period") or None,
            requires_guarantor="requires_guarantor" in form,
            is_multiple_of_savings="is_multiple_of_savings" in form,
            savings_multiplier=form.get("savings_multiplier") or None,
            requires_security="requires_security" in form,
            security_type=form.get("security_type") or None,
            security_value=form.get("security_value") or None,
            security_notes=form.get("security_notes") or None,
            requires_deposit="requires_deposit" in form,
            deposit_type=form.get("deposit_type") or None,
            deposit_value=form.get("deposit_value") or None,
            late_payment_penalty_type=form.get("late_payment_penalty_type") or None,
            late_payment_penalty_value=Decimal(form["late_payment_penalty_value"]) if form.get("late_payment_penalty_value") else None,
            requires_appraisal="requires_appraisal" in form,
            requires_board_approval="requires_board_approval" in form,
            watchful_after_days=int(form.get("watchful_after_days")) if form.get("watchful_after_days") else None,
            non_performing_after_days=int(form.get("non_performing_after_days")) if form.get("non_performing_after_days") else None,
            doubtful_after_days=int(form.get("doubtful_after_days")) if form.get("doubtful_after_days") else None,
            allows_rescheduling="allows_rescheduling" in form,
            reschedule_fee_type=form.get("reschedule_fee_type") or None,
            reschedule_fee_value=Decimal(form["reschedule_fee_value"]) if form.get("reschedule_fee_value") else None,
            allows_offset="allows_offset" in form,
            offset_covers=form.get("offset_covers") or None,
            offset_fee_type=form.get("offset_fee_type") or None,
            offset_fee_value=Decimal(form["offset_fee_value"]) if form.get("offset_fee_value") else None,
            fees=fees,
            penalties=_parse_penalties_from_form(form),
        )
        lp_crud.create_product(db, data)
        return RedirectResponse("/loan-products", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("loan_products/form.html", {
            "request": request,
            "product": None,
            "interest_methods": [e2.value for e2 in InterestMethod],
            "interest_periods": [e2.value for e2 in InterestPeriod],
            "repayment_frequencies": [e2.value for e2 in RepaymentFrequency],
            "security_types": [e2.value for e2 in SecurityType],
            "deposit_types": [e2.value for e2 in DepositType],
            "penalty_types": [e2.value for e2 in LatePaymentPenaltyType],
            "fee_types": [e2.value for e2 in FeeType],
            "error": str(e),
        })


@app.post("/loan-products/{product_id}/edit")
async def ui_update_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    product = lp_crud.get_product_by_id(db, product_id)
    form = await request.form()
    try:
        fees = _parse_fees_from_form(form)
        data = LoanProductCreate(
            product_code=product.product_code,
            product_name=form["product_name"],
            effective_date=form["effective_date"],
            interest_method=form["interest_method"],
            interest_rate=form["interest_rate"],
            interest_period=form["interest_period"],
            repayment_frequency=form["repayment_frequency"],
            max_repayment_period=form.get("max_repayment_period") or None,
            requires_guarantor="requires_guarantor" in form,
            is_multiple_of_savings="is_multiple_of_savings" in form,
            savings_multiplier=form.get("savings_multiplier") or None,
            requires_security="requires_security" in form,
            security_type=form.get("security_type") or None,
            security_value=form.get("security_value") or None,
            security_notes=form.get("security_notes") or None,
            requires_deposit="requires_deposit" in form,
            deposit_type=form.get("deposit_type") or None,
            deposit_value=form.get("deposit_value") or None,
            late_payment_penalty_type=form.get("late_payment_penalty_type") or None,
            late_payment_penalty_value=Decimal(form["late_payment_penalty_value"]) if form.get("late_payment_penalty_value") else None,
            requires_appraisal="requires_appraisal" in form,
            requires_board_approval="requires_board_approval" in form,
            watchful_after_days=int(form.get("watchful_after_days")) if form.get("watchful_after_days") else None,
            non_performing_after_days=int(form.get("non_performing_after_days")) if form.get("non_performing_after_days") else None,
            doubtful_after_days=int(form.get("doubtful_after_days")) if form.get("doubtful_after_days") else None,
            allows_rescheduling="allows_rescheduling" in form,
            reschedule_fee_type=form.get("reschedule_fee_type") or None,
            reschedule_fee_value=Decimal(form["reschedule_fee_value"]) if form.get("reschedule_fee_value") else None,
            allows_offset="allows_offset" in form,
            offset_covers=form.get("offset_covers") or None,
            offset_fee_type=form.get("offset_fee_type") or None,
            offset_fee_value=Decimal(form["offset_fee_value"]) if form.get("offset_fee_value") else None,
            fees=fees,
            penalties=_parse_penalties_from_form(form),
        )
        lp_crud.update_product(db, product.product_code, data)
        return RedirectResponse("/loan-products", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("loan_products/form.html", {
            "request": request,
            "product": product,
            "interest_methods": [e2.value for e2 in InterestMethod],
            "interest_periods": [e2.value for e2 in InterestPeriod],
            "repayment_frequencies": [e2.value for e2 in RepaymentFrequency],
            "security_types": [e2.value for e2 in SecurityType],
            "deposit_types": [e2.value for e2 in DepositType],
            "penalty_types": [e2.value for e2 in LatePaymentPenaltyType],
            "fee_types": [e2.value for e2 in FeeType],
            "error": str(e),
        })


@app.post("/loan-products/{product_id}/delete")
async def ui_loan_product_delete(product_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        lp_crud.delete_product(db, product_id)
    except Exception as e:
        print(f"Error deleting product: {e}")
    return RedirectResponse("/loan-products", status_code=303)


# ---------------------------------------------------------------------------
# Members UI
# ---------------------------------------------------------------------------

@app.get("/members", response_class=HTMLResponse)
def ui_members(request: Request, db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.id).all()
    return templates.TemplateResponse("members/list.html", {
        "request": request,
        "members": members,
    })


@app.get("/members/new", response_class=HTMLResponse)
def ui_new_member_form(request: Request):
    return templates.TemplateResponse("members/form.html", {"request": request, "member": None, "error": None})


@app.post("/members/new")
async def ui_create_member(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        member_crud.create_member(db, name=form["name"], phone=form.get("phone"), savings_balance=Decimal(form.get("savings_balance", "0")))
        return RedirectResponse("/members", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("members/form.html", {"request": request, "member": None, "error": str(e)})


@app.get("/members/{member_id}/edit", response_class=HTMLResponse)
def ui_edit_member_form(member_id: int, request: Request, db: Session = Depends(get_db)):
    member = member_crud.get_member(db, member_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return templates.TemplateResponse("members/form.html", {"request": request, "member": member, "error": None})


@app.post("/members/{member_id}/edit")
async def ui_update_member(member_id: int, request: Request, db: Session = Depends(get_db)):
    member = member_crud.get_member(db, member_id)
    form = await request.form()
    try:
        member_crud.update_member(db, member_id, name=form["name"], phone=form.get("phone"), savings_balance=Decimal(form.get("savings_balance", "0")))
        return RedirectResponse("/members", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("members/form.html", {"request": request, "member": member, "error": str(e)})


@app.post("/members/{member_id}/delete")
def ui_delete_member(member_id: int, db: Session = Depends(get_db)):
    member_crud.delete_member(db, member_id)
    return RedirectResponse("/members", status_code=303)


# ---------------------------------------------------------------------------
# Loans UI
# ---------------------------------------------------------------------------

@app.get("/loans", response_class=HTMLResponse)
def ui_loans_list(request: Request, db: Session = Depends(get_db)):
    loans = loan_crud.list_loans(db)
    return templates.TemplateResponse("loans/list.html", {
        "request": request,
        "loans": loans,
    })


@app.get("/loans/apply", response_class=HTMLResponse)
def ui_apply_loan_form(request: Request, db: Session = Depends(get_db)):
    members = db.query(Member).order_by(Member.id).all()
    products = lp_crud.list_products(db, active_only=True)
    return templates.TemplateResponse("loans/apply.html", {
        "request": request,
        "members": members,
        "products": products,
        "today": date.today().isoformat(),
        "error": None,
    })


@app.post("/loans/apply")
async def ui_apply_loan(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    members = db.query(Member).order_by(Member.id).all()
    products = lp_crud.list_products(db, active_only=True)
    try:
        data = LoanCreate(
            member_id=int(form["member_id"]),
            loan_product_id=int(form["loan_product_id"]),
            guarantor_member_id=int(form["guarantor_member_id"]) if form.get("guarantor_member_id") else None,
            principal_amount=Decimal(form["principal_amount"]),
            application_date=form["application_date"],
            disbursement_date=form.get("disbursement_date") or None,
            num_periods=int(form["num_periods"]) if form.get("num_periods") else None,
            security_provided_value=Decimal(form["security_provided_value"]) if form.get("security_provided_value") else None,
            security_provided_notes=form.get("security_provided_notes") or None,
            deposit_paid_amount=Decimal(form["deposit_paid_amount"]) if form.get("deposit_paid_amount") else None,
        )
        loan = loan_crud.create_loan(db, data)
        return RedirectResponse(f"/loans/{loan.id}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("loans/apply.html", {
            "request": request,
            "members": members,
            "products": products,
            "today": date.today().isoformat(),
            "error": str(e),
        })


@app.get("/loans/{loan_id}", response_class=HTMLResponse)
def ui_loan_detail(loan_id: int, request: Request, db: Session = Depends(get_db)):
    loan = loan_crud.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    repayments = repayment_crud.list_repayments(db, loan_id)
    ledger_entries = ledger_crud.list_transactions(db, loan_id=loan_id)
    from app.crud.loan_schedule import get_schedule
    schedule_entries = get_schedule(db, loan_id)
    return templates.TemplateResponse("loans/detail.html", {
        "request": request,
        "loan": loan,
        "repayments": repayments,
        "ledger_entries": ledger_entries,
        "schedule_entries": schedule_entries,
        "today": date.today().isoformat(),
        "error": None,
    })


@app.post("/loans/{loan_id}/approve")
async def ui_approve_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        loan_crud.approve_loan(db, loan_id)
        return RedirectResponse(f"/loans/{loan_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/loans/{loan_id}?error={str(e)}", status_code=303)


@app.post("/loans/{loan_id}/reject")
async def ui_reject_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        reason = form.get("reason", "Rejected via UI")
        loan_crud.reject_loan(db, loan_id, reason=reason)
        return RedirectResponse(f"/loans/{loan_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/loans/{loan_id}?error={str(e)}", status_code=303)


@app.post("/loans/{loan_id}/disburse")
async def ui_disburse_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        from datetime import datetime
        disburse_date = datetime.strptime(form["disbursement_date"], "%Y-%m-%d").date()
        loan_crud.disburse_loan(db, loan_id, disburse_date=disburse_date)
        return RedirectResponse(f"/loans/{loan_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/loans/{loan_id}?error={str(e)}", status_code=303)


@app.post("/loans/{loan_id}/reschedule")
async def ui_reschedule_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        from app.crud.reschedule import reschedule_loan
        from datetime import datetime
        reschedule_date = datetime.strptime(form["reschedule_date"], "%Y-%m-%d").date()
        reschedule_loan(db, loan_id, int(form["new_num_periods"]), form["reason"], reschedule_date)
        return RedirectResponse(f"/loans/{loan_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/loans/{loan_id}?error={str(e)}", status_code=303)


@app.post("/loans/{loan_id}/offset")
async def ui_offset_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        from app.crud.offset import offset_loan
        from datetime import datetime
        offset_date = datetime.strptime(form["offset_date"], "%Y-%m-%d").date()
        offset_loan(db, loan_id, offset_date)
        return RedirectResponse(f"/loans/{loan_id}", status_code=303)
    except Exception as e:
        return RedirectResponse(f"/loans/{loan_id}?error={str(e)}", status_code=303)


@app.post("/loans/{loan_id}/repayments")
async def ui_record_repayment(loan_id: int, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    loan = loan_crud.get_loan(db, loan_id)
    repayments = repayment_crud.list_repayments(db, loan_id)
    ledger_entries = ledger_crud.list_transactions(db, loan_id=loan_id)
    from app.crud.loan_schedule import get_schedule
    schedule_entries = get_schedule(db, loan_id)
    try:
        data = RepaymentCreate(
            payment_date=form["payment_date"],
            amount_paid=Decimal(form["amount_paid"]),
            notes=form.get("notes") or None,
        )
        repayment_crud.create_repayment(db, loan_id, data)
        return RedirectResponse(f"/loans/{loan_id}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("loans/detail.html", {
            "request": request,
            "loan": loan,
            "repayments": repayments,
            "ledger_entries": ledger_entries,
            "schedule_entries": schedule_entries,
            "today": date.today().isoformat(),
            "error": str(e),
        })


@app.post("/tasks/aging/run")
def trigger_aging_job(db: Session = Depends(get_db)):
    """
    Manually trigger the nightly aging job. Useful for testing or FastCron.
    """
    from app.services.aging import run_aging_job
    try:
        run_aging_job(db=db)
        return {"status": "success", "message": "Aging job completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))





# ---------------------------------------------------------------------------
# Loan Edit / Delete UI
# ---------------------------------------------------------------------------

@app.get("/loans/{loan_id}/edit", response_class=HTMLResponse)
def ui_edit_loan_form(loan_id: int, request: Request, db: Session = Depends(get_db)):
    from app.models.loan import LoanStatus
    loan = loan_crud.get_loan(db, loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return templates.TemplateResponse("loans/edit.html", {
        "request": request,
        "loan": loan,
        "statuses": [s.value for s in LoanStatus],
        "error": None,
    })


@app.post("/loans/{loan_id}/edit")
async def ui_update_loan(loan_id: int, request: Request, db: Session = Depends(get_db)):
    from app.models.loan import LoanStatus
    loan = loan_crud.get_loan(db, loan_id)
    form = await request.form()
    try:
        update_data = {
            "status": LoanStatus(form["status"]),
            "outstanding_balance": Decimal(form["outstanding_balance"]),
        }
        if form.get("guarantor_member_id"):
            update_data["guarantor_member_id"] = int(form["guarantor_member_id"])
        if form.get("security_provided_value"):
            update_data["security_provided_value"] = Decimal(form["security_provided_value"])
        if form.get("security_provided_notes"):
            update_data["security_provided_notes"] = form["security_provided_notes"]
        if form.get("deposit_paid_amount"):
            update_data["deposit_paid_amount"] = Decimal(form["deposit_paid_amount"])
        loan_crud.update_loan(db, loan_id, update_data)
        return RedirectResponse(f"/loans/{loan_id}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("loans/edit.html", {
            "request": request,
            "loan": loan,
            "statuses": [s.value for s in LoanStatus],
            "error": str(e),
        })


@app.post("/loans/{loan_id}/delete")
def ui_delete_loan(loan_id: int, db: Session = Depends(get_db)):
    loan_crud.delete_loan(db, loan_id)
    return RedirectResponse("/loans", status_code=303)


# ---------------------------------------------------------------------------
# Ledger UI
# ---------------------------------------------------------------------------

@app.get("/ledger", response_class=HTMLResponse)
def ui_ledger(
    request: Request,
    account_name: Optional[str] = None,
    loan_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    transactions = ledger_crud.list_transactions(db, account_name=account_name, loan_id=loan_id)
    return templates.TemplateResponse("ledger/list.html", {
        "request": request,
        "transactions": transactions,
        "filter_account": account_name or "",
        "filter_loan_id": loan_id or "",
        "error": None,
    })


@app.post("/ledger/manual")
async def ui_manual_transaction(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    try:
        data = ManualTransactionCreate(
            account_name=form["account_name"],
            description=form["description"],
            money_in=Decimal(form["money_in"]) if form.get("money_in") else None,
            money_out=Decimal(form["money_out"]) if form.get("money_out") else None,
            related_loan_id=int(form["related_loan_id"]) if form.get("related_loan_id") else None,
            transaction_date=form["transaction_date"],
        )
        ledger_crud.create_manual_transaction(db, data)
        return RedirectResponse("/ledger", status_code=303)
    except Exception as e:
        transactions = ledger_crud.list_transactions(db)
        return templates.TemplateResponse("ledger/list.html", {
            "request": request,
            "transactions": transactions,
            "filter_account": "",
            "filter_loan_id": "",
            "error": str(e),
        })


@app.post("/ledger/{transaction_id}/reverse")
def ui_reverse_transaction(transaction_id: int, db: Session = Depends(get_db)):
    try:
        ledger_crud.reverse_transaction(db, transaction_id)
    except ValueError:
        pass
    return RedirectResponse("/ledger", status_code=303)


# ---------------------------------------------------------------------------
# Audit Log UI
# ---------------------------------------------------------------------------

@app.get("/audit-log", response_class=HTMLResponse)
def ui_audit_log(
    request: Request,
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    entries = ledger_crud.list_audit_log(db, entity_type=entity_type)
    return templates.TemplateResponse("audit/list.html", {
        "request": request,
        "entries": entries,
        "filter_entity": entity_type or "",
    })


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_fees_from_form(form) -> list:
    """Extract fee rows from a multi-row form (fee_name[], fee_type[], etc.)."""
    fee_names = form.getlist("fee_name")
    fee_types = form.getlist("fee_type")
    fee_values = form.getlist("fee_value")
    affects_principals = form.getlist("affects_principal")
    ledger_accounts = form.getlist("ledger_account_name")

    fees = []
    for i, name in enumerate(fee_names):
        if not name.strip():
            continue
        fees.append(LoanProductFeeCreate(
            fee_name=name.strip(),
            fee_type=fee_types[i] if i < len(fee_types) else "fixed_amount",
            fee_value=Decimal(fee_values[i]) if i < len(fee_values) and fee_values[i] else Decimal("0"),
            affects_principal=str(i) in affects_principals or fee_names[i] + "_affects" in form,
            show_in_statement=True,
            ledger_account_name=ledger_accounts[i] if i < len(ledger_accounts) else name.strip() + " Account",
        ))
    return fees

from app.schemas.loan_product import LoanProductPenaltyCreate

def _parse_penalties_from_form(form) -> list:
    """Extract penalty rows from a multi-row form."""
    penalty_names = form.getlist("penalty_name")
    penalty_triggers = form.getlist("penalty_trigger")
    penalty_basis = form.getlist("penalty_basis")
    penalty_values = form.getlist("penalty_value")
    ledger_accounts = form.getlist("penalty_ledger_account_name")

    penalties = []
    for i, name in enumerate(penalty_names):
        if not name.strip():
            continue
        penalties.append(LoanProductPenaltyCreate(
            penalty_name=name.strip(),
            trigger=penalty_triggers[i] if i < len(penalty_triggers) else "late_payment",
            basis=penalty_basis[i] if i < len(penalty_basis) else "fixed_amount",
            value=Decimal(penalty_values[i]) if i < len(penalty_values) and penalty_values[i] else Decimal("0"),
            is_active=True,
            ledger_account_name=ledger_accounts[i] if i < len(ledger_accounts) else name.strip() + " Penalty Account",
        ))
    return penalties
