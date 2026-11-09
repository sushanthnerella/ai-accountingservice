import pytest
from decimal import Decimal
from datetime import date
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.bank_statement_service import BankStatementService
from backend.app.models.bank import TransactionType, ClassificationCategory

def test_extraction_arithmetic_invariants():
    # Valid: 1000 + 90 + 90 + 0 + 0 + 0 == 1180
    assert ExtractionService.validate_arithmetic_invariants(
        taxable_amount=Decimal("1000.00"),
        cgst_amount=Decimal("90.00"),
        sgst_amount=Decimal("90.00"),
        igst_amount=Decimal("0.00"),
        cess_amount=Decimal("0.00"),
        round_off_amount=Decimal("0.00"),
        total_amount=Decimal("1180.00")
    ) is True

    # Invalid: Math discrepancy > 0.05
    assert ExtractionService.validate_arithmetic_invariants(
        taxable_amount=Decimal("1000.00"),
        cgst_amount=Decimal("90.00"),
        sgst_amount=Decimal("90.00"),
        igst_amount=Decimal("0.00"),
        cess_amount=Decimal("0.00"),
        round_off_amount=Decimal("0.00"),
        total_amount=Decimal("1250.00")
    ) is False

def test_bank_statement_balance_invariant():
    txns = [
        {"type": TransactionType.CREDIT, "amount": "50000.00"},
        {"type": TransactionType.DEBIT, "amount": "15000.00"},
        {"type": TransactionType.DEBIT, "amount": "5000.00"},
    ]
    # Opening 10000 + 50000 - 15000 - 5000 = 40000
    assert BankStatementService.assert_balance_invariant(
        opening_balance=Decimal("10000.00"),
        closing_balance=Decimal("40000.00"),
        transactions=txns
    ) is True

    # Bad closing balance
    assert BankStatementService.assert_balance_invariant(
        opening_balance=Decimal("10000.00"),
        closing_balance=Decimal("45000.00"),
        transactions=txns
    ) is False

def test_narration_classifier():
    cat = BankStatementService.classify_narration("SALARY TRANSFER TO ROHAN", TransactionType.DEBIT)
    assert cat == ClassificationCategory.OPERATING_EXPENSE

    cat_gst = BankStatementService.classify_narration("GST TAX PAYMENT PMT-06 CHALLAN", TransactionType.DEBIT)
    assert cat_gst == ClassificationCategory.TAX_PAYMENT_GST

    cat_rev = BankStatementService.classify_narration("NEFT INWARD CLIENT REMITTANCE", TransactionType.CREDIT)
    assert cat_rev == ClassificationCategory.OPERATING_REVENUE
