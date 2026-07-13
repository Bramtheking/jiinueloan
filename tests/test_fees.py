"""
Tests for app/engine/fees.py

Covers spec §8:
  - The full KES 100,000 worked example (§5.4) produces exactly matching
    fee/ledger figures.
"""

from decimal import Decimal
import pytest

from app.engine.fees import (
    FeeConfig,
    compute_fees,
    compute_security_and_deposit,
    DisbursementSummary,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_fee(name, fee_type, value, ledger_account, affects_principal=False):
    return FeeConfig(
        fee_name=name,
        fee_type=fee_type,
        fee_value=Decimal(str(value)),
        affects_principal=affects_principal,
        show_in_statement=True,
        ledger_account_name=ledger_account,
    )


# ---------------------------------------------------------------------------
# §5.4 Worked Example Test (MUST PASS as acceptance test per spec)
# ---------------------------------------------------------------------------

class TestLedgerWorkedExample:
    """
    Spec §5.4:
    Loan of KES 100,000
    - Processing fee: 6% → 6,000   (Processing Fee Account, Money In)
    - Form fee:       KES 300 flat  (Form Fee Account, Money In)
    - Security deposit: 25% → 25,000 (Member Deposit General Account, Money In)
    - Loan disbursement: 100,000    (Jiinue Loan Account, Money Out)
    Total collected from member: 25,000 + 6,000 + 300 = 31,300
    """

    PRINCIPAL = Decimal("100000.00")

    def _get_fees(self):
        return [
            make_fee("Processing Fee", "percentage", 6, "Processing Fee Account"),
            make_fee("Form Fee", "fixed_amount", 300, "Form Fee Account"),
        ]

    def test_processing_fee_amount(self):
        fees = compute_fees(self.PRINCIPAL, self._get_fees())
        processing = next(f for f in fees if f.fee_name == "Processing Fee")
        assert processing.amount == Decimal("6000.00")

    def test_form_fee_amount(self):
        fees = compute_fees(self.PRINCIPAL, self._get_fees())
        form = next(f for f in fees if f.fee_name == "Form Fee")
        assert form.amount == Decimal("300.00")

    def test_security_deposit_amount(self):
        """Security = 25% of principal = 25,000."""
        result = compute_security_and_deposit(
            principal=self.PRINCIPAL,
            requires_security=True,
            security_type="percentage",
            security_value=Decimal("25"),
            requires_deposit=False,
            deposit_type=None,
            deposit_value=None,
        )
        assert result.security_amount == Decimal("25000.00")

    def test_total_collected_from_member(self):
        """
        Total collected = security + processing fee + form fee
                        = 25,000 + 6,000 + 300 = 31,300
        """
        fees = compute_fees(self.PRINCIPAL, self._get_fees())
        sec_dep = compute_security_and_deposit(
            principal=self.PRINCIPAL,
            requires_security=True,
            security_type="percentage",
            security_value=Decimal("25"),
            requires_deposit=False,
            deposit_type=None,
            deposit_value=None,
        )
        summary = DisbursementSummary(
            principal=self.PRINCIPAL,
            fees=fees,
            security_amount=sec_dep.security_amount,
            deposit_amount=sec_dep.deposit_amount,
        )
        assert summary.total_fees == Decimal("6300.00")
        assert summary.total_collected_from_member == Decimal("31300.00")

    def test_net_disbursed_equals_principal(self):
        """
        Fees don't affect principal (affects_principal=False), so
        net_disbursed == principal == 100,000.
        """
        fees = compute_fees(self.PRINCIPAL, self._get_fees())
        summary = DisbursementSummary(
            principal=self.PRINCIPAL,
            fees=fees,
            security_amount=Decimal("25000.00"),
            deposit_amount=Decimal("0.00"),
        )
        assert summary.net_disbursed == Decimal("100000.00")


# ---------------------------------------------------------------------------
# Individual Fee Cases
# ---------------------------------------------------------------------------

class TestComputeFees:
    def test_percentage_fee(self):
        cfg = [make_fee("Test", "percentage", 5, "Test Account")]
        result = compute_fees(Decimal("200000"), cfg)
        assert result[0].amount == Decimal("10000.00")

    def test_fixed_fee(self):
        cfg = [make_fee("Application", "fixed_amount", 500, "Application Account")]
        result = compute_fees(Decimal("999999"), cfg)
        assert result[0].amount == Decimal("500.00")

    def test_multiple_fees_summed(self):
        cfg = [
            make_fee("A", "percentage", 2, "Account A"),  # 2,000
            make_fee("B", "fixed_amount", 750, "Account B"),
            make_fee("C", "percentage", 1, "Account C"),  # 1,000
        ]
        results = compute_fees(Decimal("100000"), cfg)
        total = sum(r.amount for r in results)
        assert total == Decimal("3750.00")

    def test_zero_fee_value(self):
        cfg = [make_fee("Free", "fixed_amount", 0, "Free Account")]
        result = compute_fees(Decimal("50000"), cfg)
        assert result[0].amount == Decimal("0.00")

    def test_affects_principal_flag(self):
        """Fee with affects_principal=True should reduce net_disbursed."""
        cfg = [make_fee("Insurance", "percentage", 2, "Insurance Account", affects_principal=True)]
        fees = compute_fees(Decimal("100000"), cfg)
        summary = DisbursementSummary(
            principal=Decimal("100000"),
            fees=fees,
            security_amount=Decimal("0"),
            deposit_amount=Decimal("0"),
        )
        # net_disbursed = 100,000 - 2,000 = 98,000
        assert summary.net_disbursed == Decimal("98000.00")

    def test_invalid_fee_type_raises(self):
        cfg = [make_fee("Bad", "unknown_type", 5, "Account")]
        with pytest.raises(ValueError, match="Unknown fee_type"):
            compute_fees(Decimal("100000"), cfg)


# ---------------------------------------------------------------------------
# Security and Deposit
# ---------------------------------------------------------------------------

class TestSecurityAndDeposit:
    def test_percentage_security(self):
        r = compute_security_and_deposit(
            100_000, True, "percentage", Decimal("30"), False, None, None
        )
        assert r.security_amount == Decimal("30000.00")

    def test_fixed_security(self):
        r = compute_security_and_deposit(
            100_000, True, "fixed_amount", Decimal("15000"), False, None, None
        )
        assert r.security_amount == Decimal("15000.00")

    def test_custom_text_security_zero_amount(self):
        """Custom text security has no computable numeric value."""
        r = compute_security_and_deposit(
            100_000, True, "custom_text", None, False, None, None
        )
        assert r.security_amount == Decimal("0.00")

    def test_no_security_required(self):
        r = compute_security_and_deposit(
            100_000, False, None, None, False, None, None
        )
        assert r.security_amount == Decimal("0.00")

    def test_percentage_deposit(self):
        r = compute_security_and_deposit(
            100_000, False, None, None, True, "percentage", Decimal("10")
        )
        assert r.deposit_amount == Decimal("10000.00")

    def test_fixed_deposit(self):
        r = compute_security_and_deposit(
            100_000, False, None, None, True, "fixed_amount", Decimal("5000")
        )
        assert r.deposit_amount == Decimal("5000.00")
