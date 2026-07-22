"""
Aging service — runs nightly to:
1. Mark overdue loan schedule entries as missed.
2. Update loan.days_overdue.
3. Transition loan statuses: active → watchful → non_performing → doubtful.
4. Apply auto-penalties for missed payments.
5. Update member credit scores.
6. Send SMS alerts.

Called by the scheduler or directly testable as a plain function.
"""

import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.loan import Loan, LoanStatus
from app.models.loan_schedule import LoanScheduleEntry
from app.models.credit_score import MemberCreditScore
from app.models.ledger import LedgerTransaction
from app.engine.scoring import calculate_credit_score, score_label
from app.crud.audit import log_action
from app.services import sms

logger = logging.getLogger(__name__)


def run_aging_job(db: Session | None = None, today: date | None = None):
    """
    Main aging function.  Pass `db` and `today` for testing; leave None for production.
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True
    if today is None:
        today = date.today()

    try:
        _process_aging(db, today)
        db.commit()
        logger.info(f"[Aging] Completed successfully for {today}")
    except Exception as exc:
        db.rollback()
        logger.error(f"[Aging] Error: {exc}", exc_info=True)
    finally:
        if close_session:
            db.close()


def _process_aging(db: Session, today: date):
    # ── 1. Mark overdue schedule entries ──────────────────────────────────
    overdue_entries = (
        db.query(LoanScheduleEntry)
        .filter(
            LoanScheduleEntry.due_date < today,
            LoanScheduleEntry.is_paid == False,
            LoanScheduleEntry.is_missed == False,
            LoanScheduleEntry.is_cancelled == False,
        )
        .all()
    )

    missed_loan_ids = set()
    for entry in overdue_entries:
        entry.is_missed = True
        missed_loan_ids.add(entry.loan_id)
        logger.debug(f"[Aging] Loan {entry.loan_id} period {entry.period_number} marked missed")

    # ── 2. Process each active loan ────────────────────────────────────────
    active_statuses = {
        LoanStatus.active, LoanStatus.watchful,
        LoanStatus.non_performing, LoanStatus.doubtful
    }
    loans = (
        db.query(Loan)
        .filter(Loan.status.in_(active_statuses))
        .all()
    )

    for loan in loans:
        product = loan.loan_product

        # Count missed entries for this loan
        missed_count = (
            db.query(LoanScheduleEntry)
            .filter(
                LoanScheduleEntry.loan_id == loan.id,
                LoanScheduleEntry.is_missed == True,
                LoanScheduleEntry.is_cancelled == False,
            )
            .count()
        )

        # Find earliest unpaid due date to compute days_overdue
        earliest_missed = (
            db.query(LoanScheduleEntry.due_date)
            .filter(
                LoanScheduleEntry.loan_id == loan.id,
                LoanScheduleEntry.is_missed == True,
                LoanScheduleEntry.is_cancelled == False,
            )
            .order_by(LoanScheduleEntry.due_date)
            .first()
        )

        if earliest_missed:
            loan.days_overdue = (today - earliest_missed[0]).days
        else:
            loan.days_overdue = 0

        overdue_days = loan.days_overdue
        old_status = loan.status

        # ── 3. Status transitions ──────────────────────────────────────────
        new_status = old_status
        w_days = product.watchful_after_days or 30
        np_days = product.non_performing_after_days or 90
        d_days = product.doubtful_after_days or 180
        # Loss/write-off threshold = doubtful + 90 days
        loss_days = d_days + 90

        if overdue_days >= loss_days:
            new_status = LoanStatus.written_off
        elif overdue_days >= d_days:
            new_status = LoanStatus.doubtful
        elif overdue_days >= np_days:
            new_status = LoanStatus.non_performing
        elif overdue_days >= w_days:
            new_status = LoanStatus.watchful
        elif overdue_days == 0 and old_status in (LoanStatus.watchful, LoanStatus.non_performing, LoanStatus.doubtful):
            new_status = LoanStatus.active  # recovered

        if new_status != old_status:
            loan.status = new_status
            log_action(db, "loan", loan.id, f"status_changed:{old_status}→{new_status}", {
                "days_overdue": overdue_days, "triggered_by": "aging_job"
            })
            logger.info(f"[Aging] Loan {loan.loan_number}: {old_status} → {new_status}")

            # SMS alert on status change
            member = loan.member
            if new_status in (LoanStatus.watchful, LoanStatus.non_performing, LoanStatus.doubtful):
                sms.sms_missed_payment(
                    member.phone, member.name,
                    loan.loan_number, overdue_days
                )

        # ── 4. Apply auto late-payment penalty for newly missed periods ────
        if loan.id in missed_loan_ids and product.late_payment_penalty_value:
            _apply_auto_penalty(db, loan, product, today)

        # ── 5. Update credit score ─────────────────────────────────────────
        _update_credit_score(db, loan)


def _apply_auto_penalty(db: Session, loan: Loan, product, today: date):
    """Add a ledger entry for the auto-penalty on a newly missed payment."""
    from decimal import Decimal
    from app.models.loan_product import LatePaymentPenaltyType

    p_type = product.late_payment_penalty_type
    p_value = product.late_payment_penalty_value or Decimal("0")

    if p_type == LatePaymentPenaltyType.percentage:
        penalty_amount = (loan.outstanding_balance * p_value / Decimal("100")).quantize(Decimal("0.01"))
    else:
        penalty_amount = p_value

    if penalty_amount <= 0:
        return

    # Use ledger account from first active penalty config, fallback to default
    ledger_acct = "Penalty Income Account"
    if product.penalties:
        ledger_acct = product.penalties[0].ledger_account_name or ledger_acct

    tx = LedgerTransaction(
        account_name=ledger_acct,
        description=f"Auto late-payment penalty — {loan.loan_number}",
        money_in=penalty_amount,
        related_loan_id=loan.id,
        transaction_date=today,
    )
    db.add(tx)
    log_action(db, "loan", loan.id, "auto_penalty_applied", {
        "amount": str(penalty_amount), "loan_number": loan.loan_number
    })


def _update_credit_score(db: Session, loan: Loan):
    """Recalculate and persist the member's credit score based on all their repayments."""
    from app.crud.scoring import update_member_credit_score
    if loan.member_id:
        update_member_credit_score(db, loan.member_id)
