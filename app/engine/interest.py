"""
Interest calculation engine.

All functions are pure Python — no database access, no side effects.
Inputs/outputs use Decimal for exact arithmetic (no float rounding errors).

Terminology used throughout:
  - rate_pct      : interest rate as a percentage  (e.g. 20 means 20%)
  - periods       : number of repayment installments (e.g. 12 for 12 months)
  - interest_period : how often interest accrues ("monthly" | "yearly")
  - repayment_frequency : how often repayments happen ("daily"|"weekly"|"monthly"|"yearly")
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_d(value: float | int | str | Decimal) -> Decimal:
    return Decimal(str(value))


PERIODS_PER_YEAR: dict[str, Decimal] = {
    "daily":   _to_d(365),
    "weekly":  _to_d(52),
    "monthly": _to_d(12),
    "yearly":  _to_d(1),
}


def periods_per_interest_period(
    repayment_frequency: str, interest_period: str
) -> Decimal:
    """
    How many repayment periods fit inside one interest period.

    E.g. weekly repayments, monthly interest → 52/12 ≈ 4.333...
    """
    repayments_per_year = PERIODS_PER_YEAR[repayment_frequency]
    interest_periods_per_year = PERIODS_PER_YEAR[interest_period]
    return repayments_per_year / interest_periods_per_year


def round2(value: Decimal) -> Decimal:
    return value.quantize(_to_d("0.01"), rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# 1. Flat Rate
# ---------------------------------------------------------------------------

@dataclass
class FlatRateResult:
    total_interest: Decimal
    total_repayable: Decimal
    installment: Decimal          # per repayment period
    rate_used: Decimal            # decimal form (e.g. 0.20)
    time_in_interest_periods: Decimal  # e.g. 12 months


def calculate_flat_interest(
    principal: Decimal | float | int,
    rate_pct: Decimal | float | int,
    num_repayment_periods: int,
    interest_period: str,   # "monthly" | "yearly"
    repayment_frequency: str,  # "daily" | "weekly" | "monthly" | "yearly"
) -> FlatRateResult:
    """
    Flat rate: interest is always calculated on the original principal,
    never on the reducing balance.

    Formula:
        time = num_repayment_periods / (repayments_per_year / interest_periods_per_year)
             = num_repayment_periods * interest_periods_per_year / repayments_per_year
        Interest = Principal × (rate / 100) × time
        Installment = (Principal + Interest) / num_repayment_periods
    """
    P = _to_d(principal)
    r = _to_d(rate_pct) / _to_d(100)

    rpy = PERIODS_PER_YEAR[repayment_frequency]        # repayment periods per year
    ipy = PERIODS_PER_YEAR[interest_period]            # interest periods per year

    # Number of interest periods covered by the loan
    time_in_interest_periods = _to_d(num_repayment_periods) * ipy / rpy

    total_interest = P * r * time_in_interest_periods
    total_repayable = P + total_interest
    installment = total_repayable / _to_d(num_repayment_periods)

    return FlatRateResult(
        total_interest=round2(total_interest),
        total_repayable=round2(total_repayable),
        installment=round2(installment),
        rate_used=r,
        time_in_interest_periods=round2(time_in_interest_periods),
    )


# ---------------------------------------------------------------------------
# 2. Reducing Balance
# ---------------------------------------------------------------------------

@dataclass
class PeriodEntry:
    period_number: int
    opening_balance: Decimal
    interest_charge: Decimal
    principal_component: Decimal
    installment: Decimal
    closing_balance: Decimal


def calculate_reducing_balance_schedule(
    principal: Decimal | float | int,
    rate_pct: Decimal | float | int,
    num_repayment_periods: int,
    interest_period: str,   # "monthly" | "yearly"
    repayment_frequency: str,  # "daily" | "weekly" | "monthly" | "yearly"
) -> List[PeriodEntry]:
    """
    Reducing-balance (amortising) schedule.

    Each period's interest is calculated on the REMAINING balance, not the
    original principal.  The installment amount is constant (standard annuity).

    Steps:
      1. Convert annual/monthly rate to per-repayment-period rate.
         rate_per_period = rate_pct/100 / (repayments_per_year / interest_periods_per_year)
      2. Calculate constant installment using the annuity formula:
         PMT = P * r_per / (1 - (1 + r_per)^(-n))
      3. For each period: interest = balance × r_per, principal = PMT - interest.
    """
    P = _to_d(principal)
    annual_rate = _to_d(rate_pct) / _to_d(100)
    n = num_repayment_periods

    rpy = PERIODS_PER_YEAR[repayment_frequency]
    ipy = PERIODS_PER_YEAR[interest_period]

    # Rate per repayment period
    r_per = annual_rate / (rpy / ipy)  # = annual_rate * ipy / rpy

    # Annuity installment
    if r_per == 0:
        installment = P / _to_d(n)
    else:
        installment = P * r_per / (1 - (1 + r_per) ** (-n))

    schedule: List[PeriodEntry] = []
    balance = P

    for i in range(1, n + 1):
        interest_charge = balance * r_per
        principal_component = installment - interest_charge

        # Last period: mop up any rounding residual
        if i == n:
            principal_component = balance
            installment_actual = principal_component + interest_charge
        else:
            installment_actual = installment

        closing_balance = balance - principal_component
        if closing_balance < 0:
            closing_balance = _to_d(0)

        schedule.append(PeriodEntry(
            period_number=i,
            opening_balance=round2(balance),
            interest_charge=round2(interest_charge),
            principal_component=round2(principal_component),
            installment=round2(installment_actual),
            closing_balance=round2(closing_balance),
        ))
        balance = closing_balance

    return schedule


# ---------------------------------------------------------------------------
# 3. Compound Interest
# ---------------------------------------------------------------------------

@dataclass
class CompoundResult:
    total_amount: Decimal   # principal + accumulated interest
    total_interest: Decimal
    principal: Decimal
    rate_pct: Decimal
    periods: int
    interest_period: str


def calculate_compound_interest(
    principal: Decimal | float | int,
    rate_pct: Decimal | float | int,
    num_compounding_periods: int,
    interest_period: str,  # "monthly" | "yearly" — defines one compounding period
) -> CompoundResult:
    """
    Compound interest: A = P × (1 + r)^n

    Where:
      P = principal
      r = rate per compounding period (rate_pct / 100)
      n = number of compounding periods

    The spec worked example: P=100,000, r=12% yearly, n=2 years
        Year 1: 100,000 × 1.12 = 112,000
        Year 2: 112,000 × 1.12 = 125,440
    """
    P = _to_d(principal)
    r = _to_d(rate_pct) / _to_d(100)
    n = num_compounding_periods

    total_amount = P * (1 + r) ** n
    total_interest = total_amount - P

    return CompoundResult(
        total_amount=round2(total_amount),
        total_interest=round2(total_interest),
        principal=P,
        rate_pct=_to_d(rate_pct),
        periods=n,
        interest_period=interest_period,
    )


# ---------------------------------------------------------------------------
# 4. Accrued Interest on a Repayment (used at repayment time)
# ---------------------------------------------------------------------------

def calculate_accrued_interest(
    current_balance: Decimal | float | int,
    rate_pct: Decimal | float | int,
    interest_period: str,       # "monthly" | "yearly"
    days_elapsed: int,
    interest_method: str,       # "flat" | "reducing_balance" | "compound"
) -> Decimal:
    """
    Calculate interest accrued on `current_balance` over `days_elapsed` days.

    Used at the moment a repayment is recorded — we need to know how much
    interest has built up since the last repayment (or disbursement).

    For flat and reducing balance: daily interest rate is derived from the
    period rate, then multiplied by elapsed days.
    For compound: treated like reducing balance for partial-period accrual.
    """
    B = _to_d(current_balance)
    r_pct = _to_d(rate_pct)
    days = _to_d(days_elapsed)

    # Convert interest_period rate to a daily rate
    if interest_period == "monthly":
        rate_per_day = (r_pct / _to_d(100)) / _to_d(30)
    elif interest_period == "yearly":
        rate_per_day = (r_pct / _to_d(100)) / _to_d(365)
    else:
        raise ValueError(f"Unknown interest_period: {interest_period}")

    accrued = B * rate_per_day * days
    return round2(accrued)
