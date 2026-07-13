"""
Update member credit score.
"""

from sqlalchemy.orm import Session

from app.models.loan import Loan
from app.models.repayment import Repayment
from app.models.loan_schedule import LoanScheduleEntry
from app.models.credit_score import MemberCreditScore
from app.engine.scoring import calculate_credit_score, score_label


def update_member_credit_score(db: Session, member_id: int):
    """
    Recalculate and persist the member's credit score based on all their repayments.
    """
    member = db.query(MemberCreditScore).filter(MemberCreditScore.member_id == member_id).first()
    
    # We can query from loans to get status, but score is aggregate across ALL loans for this member.
    all_loans = db.query(Loan).filter(Loan.member_id == member_id).all()
    if not all_loans:
        return
        
    all_repayments = (
        db.query(Repayment)
        .join(Loan)
        .filter(Loan.member_id == member_id)
        .all()
    )

    on_time = sum(1 for r in all_repayments if not r.is_underpaid and not r.is_overpaid)
    underpaid = sum(1 for r in all_repayments if r.is_underpaid)

    missed = (
        db.query(LoanScheduleEntry)
        .join(Loan)
        .filter(
            Loan.member_id == member_id,
            LoanScheduleEntry.is_missed == True,
        )
        .count()
    )
    
    # Current status penalty depends on the worst status of any active loan
    worst_status = "active"
    status_ranks = {"written_off": 5, "doubtful": 4, "non_performing": 3, "watchful": 2, "active": 1}
    for l in all_loans:
        if l.status.value in status_ranks and status_ranks[l.status.value] > status_ranks.get(worst_status, 0):
            worst_status = l.status.value

    # Bonus for clean closure
    closed_on_time = any(l.status.value == "closed" and not any(r.is_missed for r in l.schedule_entries) for l in all_loans)

    raw_score = calculate_credit_score(
        on_time_payments=on_time,
        underpayments=underpaid,
        missed_payments=missed,
        current_loan_status=worst_status,
        closed_on_time=closed_on_time
    )

    if member is None:
        member = MemberCreditScore(member_id=member_id)
        db.add(member)

    member.score = raw_score
    member.label = score_label(raw_score)
    member.on_time_payments = on_time
    member.underpayments = underpaid
    member.missed_payments = missed
    member.loans_closed_on_time = 1 if closed_on_time else 0
    
    # No need to db.commit() here, the caller usually commits.
