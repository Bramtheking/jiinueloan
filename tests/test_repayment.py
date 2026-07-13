"""
Tests for app/engine/repayment.py

Covers spec §8:
  - Repayment order (penalty → interest → principal) allocates amounts correctly
  - Under/overpay flags
"""

from decimal import Decimal
import pytest

from app.engine.repayment import allocate_payment, AllocationResult


# ---------------------------------------------------------------------------
# Basic Allocation Order
# ---------------------------------------------------------------------------

class TestAllocationOrder:
    def test_penalty_first(self):
        """Payment covers penalty fully, then moves to interest, then principal."""
        result = allocate_payment(
            amount_paid=1_500,
            penalty_due=500,
            interest_due=700,
            outstanding_principal=10_000,
            expected_installment=2_000,
        )
        assert result.amount_to_penalty == Decimal("500.00")
        assert result.amount_to_interest == Decimal("700.00")
        assert result.amount_to_principal == Decimal("300.00")

    def test_exact_payment_clears_all(self):
        """Paying exactly the right amount should clear everything."""
        result = allocate_payment(
            amount_paid=2_200,
            penalty_due=200,
            interest_due=1_000,
            outstanding_principal=1_000,
            expected_installment=2_200,
        )
        assert result.remaining_balance_after == Decimal("0.00")
        assert result.penalty_remaining_after == Decimal("0.00")
        assert result.interest_remaining_after == Decimal("0.00")
        assert not result.is_underpaid
        assert not result.is_overpaid

    def test_payment_only_covers_penalty(self):
        """Small payment: only penalty gets covered, interest and principal untouched."""
        result = allocate_payment(
            amount_paid=300,
            penalty_due=500,
            interest_due=1_000,
            outstanding_principal=50_000,
            expected_installment=5_000,
        )
        assert result.amount_to_penalty == Decimal("300.00")
        assert result.amount_to_interest == Decimal("0.00")
        assert result.amount_to_principal == Decimal("0.00")
        assert result.penalty_remaining_after == Decimal("200.00")
        assert result.is_underpaid

    def test_payment_skips_penalty_when_none_due(self):
        """No penalty: payment goes straight to interest, then principal."""
        result = allocate_payment(
            amount_paid=3_000,
            penalty_due=0,
            interest_due=1_500,
            outstanding_principal=20_000,
            expected_installment=3_000,
        )
        assert result.amount_to_penalty == Decimal("0.00")
        assert result.amount_to_interest == Decimal("1500.00")
        assert result.amount_to_principal == Decimal("1500.00")
        assert result.remaining_balance_after == Decimal("18500.00")

    def test_allocation_totals_match_amount_paid(self):
        """The three allocation amounts should always sum to min(paid, total_owed)."""
        result = allocate_payment(
            amount_paid=5_000,
            penalty_due=200,
            interest_due=800,
            outstanding_principal=30_000,
            expected_installment=5_000,
        )
        total_allocated = (
            result.amount_to_penalty
            + result.amount_to_interest
            + result.amount_to_principal
        )
        # amount_paid = 5,000; total_owed > 5,000 so all 5,000 is allocated
        assert total_allocated == Decimal("5000.00")


# ---------------------------------------------------------------------------
# Under / Overpay Flags
# ---------------------------------------------------------------------------

class TestUnderOverpayFlags:
    def test_underpay_flagged(self):
        result = allocate_payment(
            amount_paid=1_000,
            penalty_due=0,
            interest_due=500,
            outstanding_principal=20_000,
            expected_installment=3_000,
        )
        assert result.is_underpaid is True
        assert result.is_overpaid is False

    def test_overpay_flagged(self):
        """Paying more than total owed (penalty+interest+principal) is overpayment."""
        result = allocate_payment(
            amount_paid=10_000,
            penalty_due=0,
            interest_due=500,
            outstanding_principal=5_000,
            expected_installment=5_500,
        )
        assert result.is_overpaid is True
        assert result.is_underpaid is False
        # Balance cleared to 0
        assert result.remaining_balance_after == Decimal("0.00")

    def test_exact_pay_no_flags(self):
        result = allocate_payment(
            amount_paid=5_500,
            penalty_due=0,
            interest_due=500,
            outstanding_principal=5_000,
            expected_installment=5_500,
        )
        assert result.is_underpaid is False
        assert result.is_overpaid is False

    def test_underpay_not_flagged_when_loan_cleared(self):
        """
        If the payment clears the loan (balance → 0), don't flag as underpaid
        even if it's less than expected installment.
        """
        result = allocate_payment(
            amount_paid=100,
            penalty_due=0,
            interest_due=0,
            outstanding_principal=100,
            expected_installment=500,  # normally higher installment
        )
        assert result.remaining_balance_after == Decimal("0.00")
        assert result.is_underpaid is False  # loan is cleared, doesn't matter

    def test_no_expected_installment_no_underpay_flag(self):
        """If expected_installment is not provided (0), underpay flag stays False."""
        result = allocate_payment(
            amount_paid=500,
            penalty_due=0,
            interest_due=200,
            outstanding_principal=10_000,
            expected_installment=0,
        )
        assert result.is_underpaid is False


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_zero_payment(self):
        result = allocate_payment(
            amount_paid=0,
            penalty_due=200,
            interest_due=500,
            outstanding_principal=10_000,
        )
        assert result.amount_to_penalty == Decimal("0.00")
        assert result.amount_to_interest == Decimal("0.00")
        assert result.amount_to_principal == Decimal("0.00")
        assert result.remaining_balance_after == Decimal("10000.00")

    def test_payment_exactly_clears_balance(self):
        result = allocate_payment(
            amount_paid=1_500,
            penalty_due=0,
            interest_due=500,
            outstanding_principal=1_000,
        )
        assert result.remaining_balance_after == Decimal("0.00")

    def test_no_dues_full_to_principal(self):
        """When no penalty or interest, all goes to principal."""
        result = allocate_payment(
            amount_paid=5_000,
            penalty_due=0,
            interest_due=0,
            outstanding_principal=20_000,
        )
        assert result.amount_to_principal == Decimal("5000.00")
        assert result.remaining_balance_after == Decimal("15000.00")
