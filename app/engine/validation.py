"""
Loan application validation engine.

All rules from spec §5.2.  Pure Python — no database access.
Callers pass in plain data objects; this module returns a ValidationResult.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


def _to_d(v) -> Decimal:
    return Decimal(str(v))


@dataclass
class MemberSnapshot:
    """Minimal member data needed for validation."""
    id: int
    name: str
    savings_balance: Decimal


@dataclass
class ProductSnapshot:
    """Minimal product config needed for validation."""
    is_multiple_of_savings: bool
    savings_multiplier: Optional[Decimal]
    requires_guarantor: bool
    requires_security: bool
    security_type: Optional[str]
    security_value: Optional[Decimal]
    requires_deposit: bool
    deposit_type: Optional[str]
    deposit_value: Optional[Decimal]


@dataclass
class LoanApplicationInput:
    """Everything the admin submits when applying a loan."""
    member: MemberSnapshot
    product: ProductSnapshot
    requested_principal: Decimal
    guarantor_id: Optional[int] = None           # required if product.requires_guarantor
    security_value_provided: Optional[Decimal] = None
    security_notes_provided: Optional[str] = None
    deposit_amount_provided: Optional[Decimal] = None


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_loan_application(inp: LoanApplicationInput) -> ValidationResult:
    """
    Run all product-level validation rules against a loan application.

    Rules (spec §5.2):
      1. Savings multiple check
      2. Guarantor required
      3. Security required
      4. Deposit required

    Returns a ValidationResult.  The caller decides whether to reject or proceed.
    """
    errors: list[str] = []
    warnings: list[str] = []
    m = inp.member
    p = inp.product
    principal = _to_d(inp.requested_principal)

    # --- Rule 1: Savings multiple ---
    if p.is_multiple_of_savings:
        multiplier = _to_d(p.savings_multiplier or 0)
        if multiplier <= 0:
            errors.append(
                "Product requires savings multiple but savings_multiplier is not configured."
            )
        else:
            max_allowed = _to_d(m.savings_balance) * multiplier
            if principal > max_allowed:
                errors.append(
                    f"Requested principal KES {principal:,.2f} exceeds the maximum allowed "
                    f"amount of KES {max_allowed:,.2f} "
                    f"({m.name}'s savings KES {m.savings_balance:,.2f} × {multiplier})."
                )

    # --- Rule 2: Guarantor ---
    if p.requires_guarantor:
        if inp.guarantor_id is None:
            errors.append("This product requires exactly one guarantor. No guarantor was selected.")
        elif inp.guarantor_id == inp.member.id:
            errors.append("The guarantor cannot be the same person as the borrower.")

    # --- Rule 3: Security ---
    if p.requires_security:
        if p.security_type in ("percentage", "fixed_amount"):
            # Compute required amount
            if p.security_type == "percentage":
                required = principal * (_to_d(p.security_value or 0) / _to_d(100))
            else:
                required = _to_d(p.security_value or 0)

            if inp.security_value_provided is None:
                errors.append(
                    f"This product requires security of KES {required:,.2f}. "
                    "No security value was provided."
                )
            elif _to_d(inp.security_value_provided) < required:
                errors.append(
                    f"Security provided (KES {inp.security_value_provided:,.2f}) is less than "
                    f"the required KES {required:,.2f}."
                )
        elif p.security_type == "custom_text":
            # Custom text security — just check that notes were provided
            if not inp.security_notes_provided:
                errors.append(
                    "This product requires security details (custom text). "
                    "Please provide security notes."
                )

    # --- Rule 4: Deposit ---
    if p.requires_deposit:
        if p.deposit_type in ("percentage", "fixed_amount"):
            if p.deposit_type == "percentage":
                required_deposit = principal * (_to_d(p.deposit_value or 0) / _to_d(100))
            else:
                required_deposit = _to_d(p.deposit_value or 0)

            if inp.deposit_amount_provided is None:
                errors.append(
                    f"This product requires an upfront deposit of KES {required_deposit:,.2f}."
                )
            elif _to_d(inp.deposit_amount_provided) < required_deposit:
                errors.append(
                    f"Deposit provided (KES {inp.deposit_amount_provided:,.2f}) is less than "
                    f"the required KES {required_deposit:,.2f}."
                )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )
