import uuid
from decimal import Decimal
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.invoice import Invoice, InvoiceType, ITCEligibility

class GSTService:
    @staticmethod
    def determine_tax_breakup(
        supplier_state_code: str,
        place_of_supply_state_code: str,
        taxable_amount: Decimal,
        rate_percent: Decimal = Decimal("18.00")
    ) -> Dict[str, Decimal]:
        """
        Place of Supply (POS) Rule:
        If supplier_state == pos_state -> Intrastate (CGST + SGST)
        If supplier_state != pos_state -> Interstate (IGST)
        """
        total_tax = (taxable_amount * rate_percent) / Decimal("100.00")

        if supplier_state_code == place_of_supply_state_code:
            cgst = total_tax / Decimal("2.0")
            sgst = total_tax / Decimal("2.0")
            igst = Decimal("0.0000")
        else:
            cgst = Decimal("0.0000")
            sgst = Decimal("0.0000")
            igst = total_tax

        return {
            "taxable_amount": taxable_amount,
            "cgst_amount": cgst,
            "sgst_amount": sgst,
            "igst_amount": igst,
            "total_tax": total_tax
        }

    @staticmethod
    def evaluate_itc_eligibility(hsn_or_description: str) -> ITCEligibility:
        desc_upper = hsn_or_description.upper()
        # Section 17(5) Blocked ITC rules
        if any(term in desc_upper for term in ["FOOD", "BEVERAGE", "MOTOR VEHICLE", "CATERING", "PERSONAL", "CLUB"]):
            return ITCEligibility.INELIGIBLE_SEC_17_5
        if "CAPITAL" in desc_upper or "ASSET" in desc_upper or "MACHINERY" in desc_upper:
            return ITCEligibility.ELIGIBLE_CAPITAL_GOODS
        return ITCEligibility.ELIGIBLE_INPUT_SERVICES

    @staticmethod
    async def compute_gstr_3b_summary(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID
    ) -> Dict[str, Any]:
        # 1. Outward Supplies (Sales)
        sales_q = select(Invoice).where(
            Invoice.organization_id == organization_id,
            Invoice.client_business_id == client_business_id,
            Invoice.invoice_type == InvoiceType.SALES
        )
        sales = (await db.execute(sales_q)).scalars().all()

        outward_taxable = sum(i.taxable_amount for i in sales)
        outward_cgst = sum(i.cgst_amount for i in sales)
        outward_sgst = sum(i.sgst_amount for i in sales)
        outward_igst = sum(i.igst_amount for i in sales)

        # 2. Inward Supplies (Eligible & Ineligible ITC)
        purch_q = select(Invoice).where(
            Invoice.organization_id == organization_id,
            Invoice.client_business_id == client_business_id,
            Invoice.invoice_type.in_([InvoiceType.PURCHASE, InvoiceType.EXPENSE])
        )
        purchases = (await db.execute(purch_q)).scalars().all()

        eligible_itc_cgst = sum(i.cgst_amount for i in purchases if i.itc_eligibility != ITCEligibility.INELIGIBLE_SEC_17_5)
        eligible_itc_sgst = sum(i.sgst_amount for i in purchases if i.itc_eligibility != ITCEligibility.INELIGIBLE_SEC_17_5)
        eligible_itc_igst = sum(i.igst_amount for i in purchases if i.itc_eligibility != ITCEligibility.INELIGIBLE_SEC_17_5)

        blocked_itc_cgst = sum(i.cgst_amount for i in purchases if i.itc_eligibility == ITCEligibility.INELIGIBLE_SEC_17_5)
        blocked_itc_sgst = sum(i.sgst_amount for i in purchases if i.itc_eligibility == ITCEligibility.INELIGIBLE_SEC_17_5)
        blocked_itc_igst = sum(i.igst_amount for i in purchases if i.itc_eligibility == ITCEligibility.INELIGIBLE_SEC_17_5)

        return {
            "table_3_1_outward_supplies": {
                "taxable_amount": outward_taxable,
                "cgst": outward_cgst,
                "sgst": outward_sgst,
                "igst": outward_igst,
                "total_tax": outward_cgst + outward_sgst + outward_igst
            },
            "table_4_eligible_itc": {
                "cgst": eligible_itc_cgst,
                "sgst": eligible_itc_sgst,
                "igst": eligible_itc_igst,
                "total_itc": eligible_itc_cgst + eligible_itc_sgst + eligible_itc_igst
            },
            "table_4_blocked_itc_17_5": {
                "cgst": blocked_itc_cgst,
                "sgst": blocked_itc_sgst,
                "igst": blocked_itc_igst
            },
            "net_gst_payable": {
                "cgst": max(Decimal("0.00"), outward_cgst - eligible_itc_cgst),
                "sgst": max(Decimal("0.00"), outward_sgst - eligible_itc_sgst),
                "igst": max(Decimal("0.00"), outward_igst - eligible_itc_igst)
            }
        }
