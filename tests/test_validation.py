"""
Tests for app/engine/validation.py

Covers spec §8:
  - Savings-multiple validation correctly rejects/accepts loan amounts
  - Guarantor, security, deposit rules
"""

from decimal import Decimal
import pytest

from app.engine.validation import (
    MemberSnapshot,
    ProductSnapshot,
    LoanApplicationInput,
    validate_loan_application,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_member(savings: float | str = "100000", member_id: int = 1) -> MemberSnapshot:
    return MemberSnapshot(id=member_id, name="Test Member", savings_balance=Decimal(str(savings)))


def base_product(**overrides) -> ProductSnapshot:
    defaults = dict(
        is_multiple_of_savings=False,
        savings_multiplier=None,
        requires_guarantor=False,
        requires_security=False,
        security_type=None,
        security_value=None,
        requires_deposit=False,
        deposit_type=None,
        deposit_value=None,
    )
    defaults.update(overrides)
    return ProductSnapshot(**defaults)


def apply_loan(member, product, principal, **kwargs) -> "ValidationResult":
    inp = LoanApplicationInput(
        member=member,
        product=product,
        requested_principal=Decimal(str(principal)),
        **kwargs,
    )
    return validate_loan_application(inp)


# ---------------------------------------------------------------------------
# Savings Multiple Validation
# ---------------------------------------------------------------------------

class TestSavingsMultiple:
    def test_accepts_within_limit(self):
        """100,000 savings × 3x multiplier = 300,000 max → 250,000 should pass."""
        member = make_member(savings="100000")
        product = base_product(
            is_multiple_of_savings=True,
            savings_multiplier=Decimal("3.0"),
        )
        result = apply_loan(member, product, 250_000)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_rejects_above_limit(self):
        """100,000 savings × 3x = 300,000 max → 350,000 should fail."""
        member = make_member(savings="100000")
        product = base_product(
            is_multiple_of_savings=True,
            savings_multiplier=Decimal("3.0"),
        )
        result = apply_loan(member, product, 350_000)
        assert result.is_valid is False
        assert any("exceeds" in e for e in result.errors)

    def test_accepts_exactly_at_limit(self):
        """Exactly at the limit should be accepted."""
        member = make_member(savings="100000")
        product = base_product(
            is_multiple_of_savings=True,
            savings_multiplier=Decimal("3.0"),
        )
        result = apply_loan(member, product, 300_000)
        assert result.is_valid is True

    def test_zero_savings_rejects_any_principal(self):
        """Member with zero savings cannot get any loan with savings-multiple rule."""
        member = make_member(savings="0")
        product = base_product(
            is_multiple_of_savings=True,
            savings_multiplier=Decimal("3.0"),
        )
        result = apply_loan(member, product, 1)
        assert result.is_valid is False

    def test_savings_multiple_not_required(self):
        """If product doesn't require savings multiple, any amount is fine."""
        member = make_member(savings="0")
        product = base_product(is_multiple_of_savings=False)
        result = apply_loan(member, product, 1_000_000)
        assert result.is_valid is True

    def test_missing_multiplier_config_errors(self):
        """Product misconfigured: is_multiple_of_savings=True but no multiplier."""
        member = make_member(savings="100000")
        product = base_product(is_multiple_of_savings=True, savings_multiplier=None)
        result = apply_loan(member, product, 50_000)
        assert result.is_valid is False
        assert any("not configured" in e for e in result.errors)


# ---------------------------------------------------------------------------
# Guarantor Validation
# ---------------------------------------------------------------------------

class TestGuarantor:
    def test_requires_guarantor_no_selection_fails(self):
        product = base_product(requires_guarantor=True)
        member = make_member()
        result = apply_loan(member, product, 50_000, guarantor_id=None)
        assert result.is_valid is False
        assert any("guarantor" in e.lower() for e in result.errors)

    def test_guarantor_same_as_borrower_fails(self):
        product = base_product(requires_guarantor=True)
        member = make_member(member_id=5)
        result = apply_loan(member, product, 50_000, guarantor_id=5)
        assert result.is_valid is False
        assert any("same person" in e for e in result.errors)

    def test_valid_guarantor_passes(self):
        product = base_product(requires_guarantor=True)
        member = make_member(member_id=1)
        result = apply_loan(member, product, 50_000, guarantor_id=2)
        assert result.is_valid is True

    def test_no_guarantor_required_no_error(self):
        product = base_product(requires_guarantor=False)
        member = make_member()
        result = apply_loan(member, product, 50_000, guarantor_id=None)
        assert result.is_valid is True


# ---------------------------------------------------------------------------
# Security Validation
# ---------------------------------------------------------------------------

class TestSecurity:
    def test_percentage_security_met(self):
        product = base_product(
            requires_security=True,
            security_type="percentage",
            security_value=Decimal("25"),
        )
        member = make_member()
        result = apply_loan(
            member, product, 100_000,
            security_value_provided=Decimal("25000")
        )
        assert result.is_valid is True

    def test_percentage_security_insufficient(self):
        product = base_product(
            requires_security=True,
            security_type="percentage",
            security_value=Decimal("25"),
        )
        member = make_member()
        result = apply_loan(
            member, product, 100_000,
            security_value_provided=Decimal("10000")  # need 25,000
        )
        assert result.is_valid is False
        assert any("Security provided" in e for e in result.errors)

    def test_security_not_provided_when_required_fails(self):
        product = base_product(
            requires_security=True,
            security_type="fixed_amount",
            security_value=Decimal("10000"),
        )
        member = make_member()
        result = apply_loan(member, product, 50_000, security_value_provided=None)
        assert result.is_valid is False

    def test_custom_text_security_no_notes_fails(self):
        product = base_product(
            requires_security=True,
            security_type="custom_text",
        )
        member = make_member()
        result = apply_loan(member, product, 50_000, security_notes_provided=None)
        assert result.is_valid is False

    def test_custom_text_security_with_notes_passes(self):
        product = base_product(
            requires_security=True,
            security_type="custom_text",
        )
        member = make_member()
        result = apply_loan(
            member, product, 50_000, security_notes_provided="Title deed LR123"
        )
        assert result.is_valid is True


# ---------------------------------------------------------------------------
# Deposit Validation
# ---------------------------------------------------------------------------

class TestDeposit:
    def test_percentage_deposit_met(self):
        product = base_product(
            requires_deposit=True,
            deposit_type="percentage",
            deposit_value=Decimal("10"),
        )
        member = make_member()
        result = apply_loan(member, product, 100_000, deposit_amount_provided=Decimal("10000"))
        assert result.is_valid is True

    def test_deposit_insufficient_fails(self):
        product = base_product(
            requires_deposit=True,
            deposit_type="percentage",
            deposit_value=Decimal("10"),
        )
        member = make_member()
        result = apply_loan(member, product, 100_000, deposit_amount_provided=Decimal("5000"))
        assert result.is_valid is False

    def test_deposit_not_provided_fails(self):
        product = base_product(
            requires_deposit=True,
            deposit_type="fixed_amount",
            deposit_value=Decimal("2000"),
        )
        member = make_member()
        result = apply_loan(member, product, 50_000, deposit_amount_provided=None)
        assert result.is_valid is False


# ---------------------------------------------------------------------------
# Multiple Rules Together
# ---------------------------------------------------------------------------

class TestMultipleRules:
    def test_all_rules_fail_simultaneously(self):
        """Multiple failures should return all error messages."""
        member = make_member(savings="10000", member_id=1)
        product = base_product(
            is_multiple_of_savings=True,
            savings_multiplier=Decimal("2.0"),
            requires_guarantor=True,
            requires_security=True,
            security_type="percentage",
            security_value=Decimal("25"),
        )
        result = apply_loan(
            member, product, 50_000,  # 10,000 × 2 = 20,000 max → fails
            guarantor_id=None,         # fails
            security_value_provided=None,  # fails
        )
        assert result.is_valid is False
        assert len(result.errors) == 3

    def test_clean_loan_passes_all_checks(self):
        member = make_member(savings="200000", member_id=1)
        product = base_product(
            is_multiple_of_savings=True,
            savings_multiplier=Decimal("3.0"),
            requires_guarantor=True,
            requires_security=True,
            security_type="percentage",
            security_value=Decimal("20"),
            requires_deposit=True,
            deposit_type="fixed_amount",
            deposit_value=Decimal("5000"),
        )
        result = apply_loan(
            member, product, 100_000,
            guarantor_id=2,
            security_value_provided=Decimal("20000"),
            deposit_amount_provided=Decimal("5000"),
        )
        assert result.is_valid is True
        assert result.errors == []
