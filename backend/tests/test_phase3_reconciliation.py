import pytest
from decimal import Decimal
from backend.app.services.reconciliation_service import ReconciliationService
from backend.app.models.reconciliation import TDSSection

def test_tds_match_evaluation():
    # Scenario: Invoice Total ₹1,00,000, Bank receipt ₹90,000 (10% Sec 194J)
    matched, section, tds = ReconciliationService.evaluate_tds_match(
        txn_amount=Decimal("90000.00"),
        invoice_total=Decimal("100000.00")
    )
    assert matched is True
    assert section == TDSSection.SEC_194J_PROF
    assert tds == Decimal("10000.00")

    # Scenario: Invoice Total ₹1,00,000, Bank receipt ₹98,000 (2% Sec 194J tech)
    matched_2, section_2, tds_2 = ReconciliationService.evaluate_tds_match(
        txn_amount=Decimal("98000.00"),
        invoice_total=Decimal("100000.00")
    )
    assert matched_2 is True
    assert section_2 == TDSSection.SEC_194J_TECH
    assert tds_2 == Decimal("2000.00")

    # Unmatched
    matched_none, _, _ = ReconciliationService.evaluate_tds_match(
        txn_amount=Decimal("75000.00"),
        invoice_total=Decimal("100000.00")
    )
    assert matched_none is False
