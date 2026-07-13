"""
Credit score engine — pure Python, no DB access.

Score range: 0–100
Base: 60
+3 per on-time full payment (capped at +30 → 10 good payments)
-5 per underpayment
-10 per missed payment
-20 if currently non-performing or doubtful
-10 if currently watchful
+5 if loan fully closed on time (bonus)
Floor: 0, Ceiling: 100
"""

from __future__ import annotations
from decimal import Decimal


def calculate_credit_score(
    on_time_payments: int,
    underpayments: int,
    missed_payments: int,
    current_loan_status: str | None,   # "active","watchful","non_performing","doubtful","closed","written_off"
    closed_on_time: bool = False,
) -> int:
    score = 60

    # Positive: on-time payments
    score += min(on_time_payments * 3, 30)

    # Negative: underpayments
    score -= underpayments * 5

    # Negative: missed payments
    score -= missed_payments * 10

    # Status penalty
    if current_loan_status in ("non_performing", "doubtful", "written_off"):
        score -= 20
    elif current_loan_status == "watchful":
        score -= 10

    # Bonus for clean closure
    if closed_on_time:
        score += 5

    return max(0, min(100, score))


def score_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Good"
    elif score >= 50:
        return "Fair"
    elif score >= 35:
        return "Poor"
    else:
        return "High Risk"
