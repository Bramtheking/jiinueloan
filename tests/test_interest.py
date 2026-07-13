"""
Tests for app/engine/interest.py

Covers spec §8:
  - Flat rate interest calculation matches formula
  - Reducing balance recalculates correctly per period
  - Compound interest: 100,000 → 112,000 → 125,440 (12% yearly, 2 years)
"""

from decimal import Decimal
import pytest

from app.engine.interest import (
    calculate_flat_interest,
    calculate_reducing_balance_schedule,
    calculate_compound_interest,
    calculate_accrued_interest,
    round2,
)


# ---------------------------------------------------------------------------
# Flat rate
# ---------------------------------------------------------------------------

class TestFlatRate:
    def test_basic_formula(self):
        """
        Principal=100,000 @ 20%/month, 12 monthly repayments.
        Time = 12 months.
        Interest = 100,000 × 0.20 × 12 = 240,000   ← 12 months at 20%
        Installment = (100,000 + 240,000) / 12 = 28,333.33
        """
        result = calculate_flat_interest(
            principal=100_000,
            rate_pct=20,
            num_repayment_periods=12,
            interest_period="monthly",
            repayment_frequency="monthly",
        )
        assert result.total_interest == Decimal("240000.00")
        assert result.total_repayable == Decimal("340000.00")
        assert result.installment == Decimal("28333.33")

    def test_weekly_repayments_monthly_interest(self):
        """
        Principal=50,000 @ 10%/month, 8 weekly repayments.
        Time in months = 8 weeks / (52 weeks/12 months) = 8 × 12/52 ≈ 1.846 months
        Interest = 50,000 × 0.10 × (8 × 12/52)
        """
        result = calculate_flat_interest(
            principal=50_000,
            rate_pct=10,
            num_repayment_periods=8,
            interest_period="monthly",
            repayment_frequency="weekly",
        )
        # time = 8 * 12/52 = 96/52
        time = Decimal("8") * Decimal("12") / Decimal("52")
        expected_interest = round2(Decimal("50000") * Decimal("0.10") * time)
        assert result.total_interest == expected_interest

    def test_yearly_rate_monthly_repayments(self):
        """
        Principal=120,000 @ 12%/year, 12 monthly repayments.
        Time = 1 year.
        Interest = 120,000 × 0.12 × 1 = 14,400
        Installment = 134,400 / 12 = 11,200.00
        """
        result = calculate_flat_interest(
            principal=120_000,
            rate_pct=12,
            num_repayment_periods=12,
            interest_period="yearly",
            repayment_frequency="monthly",
        )
        assert result.total_interest == Decimal("14400.00")
        assert result.installment == Decimal("11200.00")

    def test_zero_rate(self):
        """Zero rate: total interest should be zero, installment = P/n."""
        result = calculate_flat_interest(
            principal=30_000,
            rate_pct=0,
            num_repayment_periods=6,
            interest_period="monthly",
            repayment_frequency="monthly",
        )
        assert result.total_interest == Decimal("0.00")
        assert result.installment == Decimal("5000.00")


# ---------------------------------------------------------------------------
# Reducing Balance
# ---------------------------------------------------------------------------

class TestReducingBalance:
    def test_schedule_length(self):
        """Schedule should have exactly n entries."""
        schedule = calculate_reducing_balance_schedule(
            principal=100_000,
            rate_pct=20,
            num_repayment_periods=6,
            interest_period="monthly",
            repayment_frequency="monthly",
        )
        assert len(schedule) == 6

    def test_interest_decreases_each_period(self):
        """Reducing-balance → interest charge must decrease each period."""
        schedule = calculate_reducing_balance_schedule(
            principal=100_000,
            rate_pct=24,
            num_repayment_periods=12,
            interest_period="yearly",
            repayment_frequency="monthly",
        )
        for i in range(len(schedule) - 1):
            assert schedule[i].interest_charge >= schedule[i + 1].interest_charge, (
                f"Interest should not increase: period {i+1}={schedule[i].interest_charge} "
                f"vs {i+2}={schedule[i+1].interest_charge}"
            )

    def test_final_balance_is_zero(self):
        """After all repayments the loan should be paid off."""
        schedule = calculate_reducing_balance_schedule(
            principal=100_000,
            rate_pct=20,
            num_repayment_periods=12,
            interest_period="monthly",
            repayment_frequency="monthly",
        )
        assert schedule[-1].closing_balance == Decimal("0.00")

    def test_opening_balance_chain(self):
        """Each period's opening balance == previous period's closing balance."""
        schedule = calculate_reducing_balance_schedule(
            principal=50_000,
            rate_pct=18,
            num_repayment_periods=6,
            interest_period="yearly",
            repayment_frequency="monthly",
        )
        for i in range(1, len(schedule)):
            assert schedule[i].opening_balance == schedule[i - 1].closing_balance, (
                f"Balance chain broken at period {i+1}"
            )

    def test_weekly_reducing_balance(self):
        """Weekly repayments, monthly rate — schedule length and zero final balance."""
        schedule = calculate_reducing_balance_schedule(
            principal=20_000,
            rate_pct=5,
            num_repayment_periods=4,
            interest_period="monthly",
            repayment_frequency="weekly",
        )
        assert len(schedule) == 4
        assert schedule[-1].closing_balance == Decimal("0.00")


# ---------------------------------------------------------------------------
# Compound Interest (spec §8 worked example)
# ---------------------------------------------------------------------------

class TestCompoundInterest:
    def test_spec_worked_example(self):
        """
        Spec §8: P=100,000, r=12%/year, 2 yearly compounding periods.
        Year 1: 100,000 × 1.12 = 112,000
        Year 2: 112,000 × 1.12 = 125,440
        """
        result = calculate_compound_interest(
            principal=100_000,
            rate_pct=12,
            num_compounding_periods=2,
            interest_period="yearly",
        )
        assert result.total_amount == Decimal("125440.00")
        assert result.total_interest == Decimal("25440.00")

    def test_single_period(self):
        """1 period: A = P × (1 + r)."""
        result = calculate_compound_interest(
            principal=100_000,
            rate_pct=12,
            num_compounding_periods=1,
            interest_period="yearly",
        )
        assert result.total_amount == Decimal("112000.00")

    def test_zero_rate(self):
        """Zero rate compound: total_amount == principal."""
        result = calculate_compound_interest(
            principal=50_000,
            rate_pct=0,
            num_compounding_periods=5,
            interest_period="yearly",
        )
        assert result.total_amount == Decimal("50000.00")
        assert result.total_interest == Decimal("0.00")


# ---------------------------------------------------------------------------
# Accrued Interest
# ---------------------------------------------------------------------------

class TestAccruedInterest:
    def test_monthly_rate_30_days(self):
        """
        Balance=100,000 @ 20%/month, 30 days elapsed.
        daily rate = 0.20 / 30 = 0.006667
        accrued = 100,000 × 0.006667 × 30 = 20,000
        """
        accrued = calculate_accrued_interest(
            current_balance=100_000,
            rate_pct=20,
            interest_period="monthly",
            days_elapsed=30,
            interest_method="reducing_balance",
        )
        assert accrued == Decimal("20000.00")

    def test_yearly_rate_365_days(self):
        """
        Balance=100,000 @ 12%/year, 365 days → full year → interest = 12,000.
        """
        accrued = calculate_accrued_interest(
            current_balance=100_000,
            rate_pct=12,
            interest_period="yearly",
            days_elapsed=365,
            interest_method="flat",
        )
        assert accrued == Decimal("12000.00")
