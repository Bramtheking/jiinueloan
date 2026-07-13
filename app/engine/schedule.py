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
        # Flat rate: split each installment into equal interest + principal
        total_interest = result.total_interest
        interest_per_period = round2(total_interest / _to_d(num_periods))
        principal_per_period = round2(
            (principal + total_interest - interest_per_period * _to_d(num_periods - 1)
             if True else installment - interest_per_period)
        )
        balance = principal
        for i in range(1, num_periods + 1):
            due = _add_periods(disbursement_date, repayment_frequency, i)
            if i == num_periods:
                p = balance
                inst = round2(p + interest_per_period)
            else:
                p = round2(installment - interest_per_period)
                inst = installment
            closing = round2(balance - p)
            entries.append(ScheduleEntry(
                period_number=i,
                due_date=due,
                expected_amount=inst,
                expected_principal=p,
                expected_interest=interest_per_period,
                opening_balance=round2(balance),
                closing_balance=closing if closing > 0 else _to_d(0),
            ))
            balance = closing if closing > 0 else _to_d(0)

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
        # For compound: treat like flat for schedule purposes
        # (total amount / num_periods = equal installments)
        result = calculate_compound_interest(
            principal, interest_rate_pct, num_periods, interest_period
        )
        total_repayable = result.total_amount
        installment = round2(total_repayable / _to_d(num_periods))
        interest_per_period = round2(result.total_interest / _to_d(num_periods))
        balance = principal
        for i in range(1, num_periods + 1):
            due = _add_periods(disbursement_date, repayment_frequency, i)
            p = round2(installment - interest_per_period)
            closing = round2(balance - p)
            entries.append(ScheduleEntry(
                period_number=i,
                due_date=due,
                expected_amount=installment,
                expected_principal=p,
                expected_interest=interest_per_period,
                opening_balance=round2(balance),
                closing_balance=closing if closing > 0 else _to_d(0),
            ))
            balance = closing if closing > 0 else _to_d(0)

    else:
        raise ValueError(f"Unknown interest_method: {interest_method}")

    return entries
