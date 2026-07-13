"""
Repayment allocation engine.

Allocates an incoming payment to:  penalty → interest → principal
(in that fixed priority order, per spec §5.3)

Pure Python — no database access.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


def _to_d(v) -> Decimal:
    return Decimal(str(v))


def round2(v: Decimal) -> Decimal:
    return v.quantize(_to_d("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class AllocationResult:
    """Breakdown of how a payment was applied."""
    amount_paid: Decimal

    amount_to_penalty: Decimal
    amount_to_interest: Decimal
    amount_to_principal: Decimal

    remaining_balance_after: Decimal   # outstanding principal after this payment

    penalty_remaining_after: Decimal   # any unpaid penalty carried forward
    interest_remaining_after: Decimal  # any unpaid interest carried forward

    is_underpaid: bool   # paid less than the expected installment
    is_overpaid: bool    # paid more than needed to clear everything

    @property
    def total_allocated(self) -> Decimal:
        return (
            self.amount_to_penalty
            + self.amount_to_interest
            + self.amount_to_principal
        )


def allocate_payment(
    amount_paid: Decimal | float | int,
    penalty_due: Decimal | float | int,
    interest_due: Decimal | float | int,
    outstanding_principal: Decimal | float | int,
    expected_installment: Decimal | float | int = Decimal("0"),
) -> AllocationResult:
    """
    Allocate `amount_paid` in the order: penalty → interest → principal.

    Parameters
    ----------
    amount_paid:           Cash received from member this period.
    penalty_due:           Penalty charges outstanding (late fees, etc.).
    interest_due:          Interest accrued since last payment or disbursement.
    outstanding_principal: Remaining principal balance before this payment.
    expected_installment:  What the member *should* have paid (for under/overpay flags).

    Returns
    -------
    AllocationResult with full breakdown.
    """
    paid = _to_d(amount_paid)
    penalty = _to_d(penalty_due)
    interest = _to_d(interest_due)
    principal = _to_d(outstanding_principal)
    expected = _to_d(expected_installment)

    remaining = paid

    # 1. Apply to penalty first
    to_penalty = min(remaining, penalty)
    remaining -= to_penalty
    penalty_left = penalty - to_penalty

    # 2. Apply to interest
    to_interest = min(remaining, interest)
    remaining -= to_interest
    interest_left = interest - to_interest

    # 3. Apply to principal
    to_principal = min(remaining, principal)
    remaining -= to_principal  # remaining now = overpayment (excess cash)

    new_balance = round2(principal - to_principal)

    # Overpaid if there is still cash left after clearing everything
    total_owed = penalty + interest + principal
    is_overpaid = paid > total_owed
    # Underpaid if paid less than expected installment (and loan not fully cleared)
    is_underpaid = (expected > 0 and paid < expected and new_balance > 0)

    return AllocationResult(
        amount_paid=round2(paid),
        amount_to_penalty=round2(to_penalty),
        amount_to_interest=round2(to_interest),
        amount_to_principal=round2(to_principal),
        remaining_balance_after=new_balance,
        penalty_remaining_after=round2(penalty_left),
        interest_remaining_after=round2(interest_left),
        is_underpaid=is_underpaid,
        is_overpaid=is_overpaid,
    )
