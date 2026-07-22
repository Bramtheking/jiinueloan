"""
Repayment schedule generator.

Given a loan's principal, product config, and disbursement date,
returns a list of (period_number, due_date, expected_amount) rows.

Pure Python — no DB access.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from dateutil.relativedelta import relativedelta

from app.engine.interest import (
    calculate_flat_interest,
    calculate_reducing_balance_schedule,
    calculate_compound_interest,
    round2,
    _to_d,
)


@dataclass
class ScheduleEntry:
    period_number: int
    due_date: date
    expected_amount: Decimal      # total installment due
    expected_principal: Decimal
    expected_interest: Decimal
    opening_balance: Decimal
    closing_balance: Decimal


def _add_periods(start: date, frequency: str, n: int) -> date:
    """Advance `start` by n repayment periods."""
    if frequency == "daily":
        return start + timedelta(days=n)
    elif frequency == "weekly":
        return start + timedelta(weeks=n)
    elif frequency == "monthly":
        return start + relativedelta(months=n)
    elif frequency == "yearly":
        return start + relativedelta(years=n)
    raise ValueError(f"Unknown frequency: {frequency}")


def generate_schedule(
    principal: Decimal,
    interest_rate_pct: Decimal,
    interest_period: str,          # "monthly" | "yearly"
    interest_method: str,          # "flat" | "reducing_balance" | "compound"
    repayment_frequency: str,      # "daily" | "weekly" | "monthly" | "yearly"
    num_periods: int,
    disbursement_date: date,
) -> list[ScheduleEntry]:
    """
    Generate the full repayment schedule for a loan.
    First due date = disbursement_date + 1 period.
    """
    entries: list[ScheduleEntry] = []

    if interest_method == "flat":
        result = calculate_flat_interest(
            principal, interest_rate_pct, num_periods,
            interest_period, repayment_frequency
        )
        installment = result.installment
        interest_per_period = round2(result.total_interest / _to_d(num_periods))
        principal_per_period = round2(principal / _to_d(num_periods))
        balance = principal
        for i in range(1, num_periods + 1):
            due = _add_periods(disbursement_date, repayment_frequency, i)
            if i == num_periods:
                # Last period: mop up any rounding residual
                p = balance
                inst = round2(p + interest_per_period)
            else:
                p = principal_per_period
                inst = installment
            closing = round2(balance - p)
            if closing < 0:
                closing = _to_d(0)
            entries.append(ScheduleEntry(
                period_number=i,
                due_date=due,
                expected_amount=inst,
                expected_principal=p,
                expected_interest=interest_per_period,
                opening_balance=round2(balance),
                closing_balance=closing,
            ))
            balance = closing

    elif interest_method == "reducing_balance":
        schedule = calculate_reducing_balance_schedule(
            principal, interest_rate_pct, num_periods,
            interest_period, repayment_frequency
        )
        for i, row in enumerate(schedule, 1):
            due = _add_periods(disbursement_date, repayment_frequency, i)
            entries.append(ScheduleEntry(
                period_number=i,
                due_date=due,
                expected_amount=row.installment,
                expected_principal=row.principal_component,
                expected_interest=row.interest_charge,
                opening_balance=row.opening_balance,
                closing_balance=row.closing_balance,
            ))

    elif interest_method == "compound":
        # True compound amortization:
        # Each period compounds on remaining balance, equal installments (annuity formula).
        # This is identical to reducing balance but with rate compounded per period.
        from app.engine.interest import PERIODS_PER_YEAR
        P = principal
        r_pct = interest_rate_pct
        ipy = PERIODS_PER_YEAR[interest_period]
        rpy = PERIODS_PER_YEAR[repayment_frequency]
        # Compound rate per repayment period
        r_annual = _to_d(r_pct) / _to_d(100)
        r_per = (1 + r_annual / ipy) ** (ipy / rpy) - 1

        if r_per == 0:
            installment = round2(P / _to_d(num_periods))
        else:
            installment = round2(P * r_per / (1 - (1 + r_per) ** (-num_periods)))

        balance = P
        for i in range(1, num_periods + 1):
            due = _add_periods(disbursement_date, repayment_frequency, i)
            interest_charge = round2(balance * r_per)
            principal_component = round2(installment - interest_charge)
            if i == num_periods:
                principal_component = balance
                installment_actual = round2(principal_component + interest_charge)
            else:
                installment_actual = installment
            closing = round2(balance - principal_component)
            if closing < 0:
                closing = _to_d(0)
            entries.append(ScheduleEntry(
                period_number=i,
                due_date=due,
                expected_amount=installment_actual,
                expected_principal=principal_component,
                expected_interest=interest_charge,
                opening_balance=round2(balance),
                closing_balance=closing,
            ))
            balance = closing

    else:
        raise ValueError(f"Unknown interest_method: {interest_method}")

    return entries
