import pytest
from decimal import Decimal
from backend.app.services.gst_service import GSTService
from backend.app.models.invoice import ITCEligibility

def test_gst_place_of_supply():
    # Intrastate (27 -> 27): CGST + SGST (9% + 9%)
    intra = GSTService.determine_tax_breakup("27", "27", Decimal("10000.00"), Decimal("18.00"))
    assert intra["cgst_amount"] == Decimal("900.00")
    assert intra["sgst_amount"] == Decimal("900.00")
    assert intra["igst_amount"] == Decimal("0.00")

    # Interstate (27 -> 29): IGST 18%
    inter = GSTService.determine_tax_breakup("27", "29", Decimal("10000.00"), Decimal("18.00"))
    assert inter["cgst_amount"] == Decimal("0.00")
    assert inter["sgst_amount"] == Decimal("0.00")
    assert inter["igst_amount"] == Decimal("1800.00")

def test_blocked_itc_rules():
    assert GSTService.evaluate_itc_eligibility("Client catering and food expenses") == ITCEligibility.INELIGIBLE_SEC_17_5
    assert GSTService.evaluate_itc_eligibility("Motor vehicle petrol expense") == ITCEligibility.INELIGIBLE_SEC_17_5
    assert GSTService.evaluate_itc_eligibility("AWS Cloud Server hosting") == ITCEligibility.ELIGIBLE_INPUT_SERVICES
    assert GSTService.evaluate_itc_eligibility("Office Laptop Computer Machinery Asset") == ITCEligibility.ELIGIBLE_CAPITAL_GOODS
