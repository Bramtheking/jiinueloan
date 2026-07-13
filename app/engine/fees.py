"""
Fee computation engine.

Calculates per-fee amounts for a loan application based on the product's
fee configuration.  Pure Python — no DB access.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import List


def _to_d(v) -> Decimal:
    return Decimal(str(v))


def round2(v: Decimal) -> Decimal:
    return v.quantize(_to_d("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class FeeConfig:
    """Mirrors LoanProductFee — passed in from the caller without DB access."""
    fee_name: str
    fee_type: str          # "percentage" | "fixed_amount"
    fee_value: Decimal
    affects_principal: bool
    show_in_statement: bool
    ledger_account_name: str


@dataclass
class FeeResult:
    fee_name: str
    amount: Decimal
    ledger_account_name: str
    affects_principal: bool
    show_in_statement: bool


def compute_fees(
    principal: Decimal | float | int,
    fee_configs: List[FeeConfig],
) -> List[FeeResult]:
    """
    Compute the monetary amount for each fee against `principal`.

    fee_type=="percentage"   → amount = principal × (fee_value / 100)
    fee_type=="fixed_amount" → amount = fee_value  (unchanged)
    """
    P = _to_d(principal)
    results: List[FeeResult] = []

    for cfg in fee_configs:
        if cfg.fee_type == "percentage":
            amount = round2(P * (_to_d(cfg.fee_value) / _to_d(100)))
        elif cfg.fee_type == "fixed_amount":
            amount = round2(_to_d(cfg.fee_value))
        else:
            raise ValueError(f"Unknown fee_type: {cfg.fee_type!r}")

        results.append(FeeResult(
            fee_name=cfg.fee_name,
            amount=amount,
            ledger_account_name=cfg.ledger_account_name,
            affects_principal=cfg.affects_principal,
            show_in_statement=cfg.show_in_statement,
        ))

    return results


@dataclass
class SecurityDepositResult:
    """Computed security and deposit amounts for a loan application."""
    security_amount: Decimal    # what collateral is required (informational)
    deposit_amount: Decimal     # upfront deposit collected (Money In to SACCO)


def compute_security_and_deposit(
    principal: Decimal | float | int,
    requires_security: bool,
    security_type: str | None,        # "percentage"|"fixed_amount"|"custom_text"
    security_value: Decimal | None,
    requires_deposit: bool,
    deposit_type: str | None,         # "percentage"|"fixed_amount"
    deposit_value: Decimal | None,
) -> SecurityDepositResult:
    """
    Calculate the security requirement and required deposit amounts.

    Security is collateral (e.g. a physical asset or cash held aside).
    Deposit is cash actually collected upfront by the SACCO.
    """
    P = _to_d(principal)

    # --- Security ---
    security_amount = _to_d(0)
    if requires_security and security_type in ("percentage", "fixed_amount"):
        if security_type == "percentage":
            security_amount = round2(P * (_to_d(security_value or 0) / _to_d(100)))
        else:  # fixed_amount
            security_amount = round2(_to_d(security_value or 0))
    # custom_text → no computable amount, security_amount stays 0

    # --- Deposit ---
    deposit_amount = _to_d(0)
    if requires_deposit and deposit_type in ("percentage", "fixed_amount"):
        if deposit_type == "percentage":
            deposit_amount = round2(P * (_to_d(deposit_value or 0) / _to_d(100)))
        else:  # fixed_amount
            deposit_amount = round2(_to_d(deposit_value or 0))

    return SecurityDepositResult(
        security_amount=security_amount,
        deposit_amount=deposit_amount,
    )


@dataclass
class DisbursementSummary:
    """
    Complete summary of what happens at loan disbursement.
    Matches the worked example in spec §5.4.
    """
    principal: Decimal
    fees: List[FeeResult]
    security_amount: Decimal
    deposit_amount: Decimal

    @property
    def total_fees(self) -> Decimal:
        return sum((f.amount for f in self.fees), Decimal("0"))

    @property
    def total_collected_from_member(self) -> Decimal:
        """Sum of everything the member must bring/have collected at disbursement."""
        return self.security_amount + self.deposit_amount + self.total_fees

    @property
    def net_disbursed(self) -> Decimal:
        """Actual cash sent to the member — principal minus any affects_principal fees."""
        deductions = sum(
            (f.amount for f in self.fees if f.affects_principal), Decimal("0")
        )
        return self.principal - deductions
