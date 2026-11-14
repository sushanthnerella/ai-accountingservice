import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.invoice import Invoice, InvoiceType, ITCEligibility
from backend.app.models.client_business import ClientBusiness

TWO_PLACES = Decimal("0.01")
FOUR_PLACES = Decimal("0.0001")

class GSTService:
    @staticmethod
    def extract_state_code_from_gstin(gstin: Optional[str], default: str = "27") -> str:
        if gstin and len(gstin) >= 2 and gstin[:2].isdigit():
            return gstin[:2]
        return default

    @staticmethod
    def determine_tax_breakup(
        supplier_state_code: str,
        place_of_supply_state_code: str,
        taxable_amount: Decimal,
        rate_percent: Decimal = Decimal("18.00")
    ) -> Dict[str, Decimal]:
        """
        Statutory Place of Supply (POS) Rule:
        - If supplier_state == pos_state -> Intra-state: CGST = rate/2, SGST = rate/2, IGST = 0
        - If supplier_state != pos_state -> Inter-state: IGST = rate, CGST = 0, SGST = 0
        All computations use Decimal with ROUND_HALF_UP precision.
        """
        taxable = taxable_amount.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        rate = rate_percent.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        if supplier_state_code == place_of_supply_state_code:
            # Intra-state: 50% CGST + 50% SGST
            half_rate = rate / Decimal("2.0")
            cgst = ((taxable * half_rate) / Decimal("100.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            sgst = ((taxable * half_rate) / Decimal("100.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            igst = Decimal("0.00")
            total_tax = cgst + sgst
        else:
            # Inter-state: 100% IGST
            cgst = Decimal("0.00")
            sgst = Decimal("0.00")
            igst = ((taxable * rate) / Decimal("100.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            total_tax = igst

        return {
            "taxable_amount": taxable,
            "cgst_amount": cgst,
            "sgst_amount": sgst,
            "igst_amount": igst,
            "total_tax": total_tax
        }

    @staticmethod
    def calculate_multi_slab_invoice_taxes(
        supplier_gstin: Optional[str],
        client_gstin: Optional[str],
        line_items: List[Dict[str, Any]],
        is_reverse_charge: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates multi-slab GST across line items (0%, 5%, 12%, 18%, 28%),
        enforcing intra-state vs inter-state rules and calculating exact round_off.
        """
        supp_state = GSTService.extract_state_code_from_gstin(supplier_gstin, "27")
        client_state = GSTService.extract_state_code_from_gstin(client_gstin, supp_state)

        total_taxable = Decimal("0.00")
        total_cgst = Decimal("0.00")
        total_sgst = Decimal("0.00")
        total_igst = Decimal("0.00")

        processed_items = []
        for item in line_items:
            t_amt = Decimal(str(item.get("taxable_amount", "0.00"))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            rate = Decimal(str(item.get("tax_rate_percent", item.get("gst_rate", "18.00")))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

            breakup = GSTService.determine_tax_breakup(supp_state, client_state, t_amt, rate)
            total_taxable += breakup["taxable_amount"]
            total_cgst += breakup["cgst_amount"]
            total_sgst += breakup["sgst_amount"]
            total_igst += breakup["igst_amount"]

            item_dict = dict(item)
            item_dict["cgst"] = breakup["cgst_amount"]
            item_dict["sgst"] = breakup["sgst_amount"]
            item_dict["igst"] = breakup["igst_amount"]
            processed_items.append(item_dict)

        subtotal = total_taxable + total_cgst + total_sgst + total_igst
        rounded_total = subtotal.quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)
        round_off = (rounded_total - subtotal).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        return {
            "supplier_state_code": supp_state,
            "client_state_code": client_state,
            "is_intrastate": (supp_state == client_state),
            "taxable_amount": total_taxable,
            "cgst_amount": total_cgst,
            "sgst_amount": total_sgst,
            "igst_amount": total_igst,
            "total_tax": total_cgst + total_sgst + total_igst,
            "round_off_amount": round_off,
            "total_amount": rounded_total,
            "is_reverse_charge": is_reverse_charge,
            "processed_items": processed_items
        }

    @staticmethod
    def evaluate_itc_eligibility(hsn_or_description: str) -> ITCEligibility:
        desc_upper = (hsn_or_description or "").upper()
        # Section 17(5) Blocked ITC rules
        if any(term in desc_upper for term in ["FOOD", "BEVERAGE", "MOTOR VEHICLE", "CATERING", "PERSONAL", "CLUB", "BEAUTY"]):
            return ITCEligibility.INELIGIBLE_SEC_17_5
        if any(term in desc_upper for term in ["CAPITAL", "ASSET", "MACHINERY", "EQUIPMENT", "COMPUTER", "LAPTOP"]):
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

        outward_taxable = sum((i.taxable_amount for i in sales), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        outward_cgst = sum((i.cgst_amount for i in sales), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        outward_sgst = sum((i.sgst_amount for i in sales), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        outward_igst = sum((i.igst_amount for i in sales), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # 2. Inward Supplies (Purchases & Expenses)
        purch_q = select(Invoice).where(
            Invoice.organization_id == organization_id,
            Invoice.client_business_id == client_business_id,
            Invoice.invoice_type.in_([InvoiceType.PURCHASE, InvoiceType.EXPENSE])
        )
        purchases = (await db.execute(purch_q)).scalars().all()

        # Eligible ITC
        eligible_purchases = [p for p in purchases if p.itc_eligibility != ITCEligibility.INELIGIBLE_SEC_17_5 and not p.is_reverse_charge]
        eligible_itc_cgst = sum((i.cgst_amount for i in eligible_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        eligible_itc_sgst = sum((i.sgst_amount for i in eligible_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        eligible_itc_igst = sum((i.igst_amount for i in eligible_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # Ineligible / Blocked ITC under Section 17(5)
        blocked_purchases = [p for p in purchases if p.itc_eligibility == ITCEligibility.INELIGIBLE_SEC_17_5]
        blocked_itc_cgst = sum((i.cgst_amount for i in blocked_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        blocked_itc_sgst = sum((i.sgst_amount for i in blocked_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        blocked_itc_igst = sum((i.igst_amount for i in blocked_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # Reverse Charge Mechanism (RCM) Inward Supplies (Table 3.1(d))
        rcm_purchases = [p for p in purchases if p.is_reverse_charge]
        rcm_taxable = sum((i.taxable_amount for i in rcm_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        rcm_cgst = sum((i.cgst_amount for i in rcm_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        rcm_sgst = sum((i.sgst_amount for i in rcm_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        rcm_igst = sum((i.igst_amount for i in rcm_purchases), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        # Net GST Payable
        # Output tax liability (Table 3.1 outward + Table 3.1.d RCM liability) minus eligible ITC
        net_cgst = max(Decimal("0.00"), (outward_cgst + rcm_cgst) - eligible_itc_cgst)
        net_sgst = max(Decimal("0.00"), (outward_sgst + rcm_sgst) - eligible_itc_sgst)
        net_igst = max(Decimal("0.00"), (outward_igst + rcm_igst) - eligible_itc_igst)

        return {
            "table_3_1_outward_supplies": {
                "taxable_amount": outward_taxable,
                "cgst": outward_cgst,
                "sgst": outward_sgst,
                "igst": outward_igst,
                "total_tax": outward_cgst + outward_sgst + outward_igst
            },
            "table_3_1_d_inward_rcm_supplies": {
                "taxable_amount": rcm_taxable,
                "cgst": rcm_cgst,
                "sgst": rcm_sgst,
                "igst": rcm_igst,
                "total_rcm_liability": rcm_cgst + rcm_sgst + rcm_igst
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
                "igst": blocked_itc_igst,
                "total_blocked_itc": blocked_itc_cgst + blocked_itc_sgst + blocked_itc_igst
            },
            "net_gst_payable": {
                "cgst": net_cgst,
                "sgst": net_sgst,
                "igst": net_igst,
                "total": net_cgst + net_sgst + net_igst
            }
        }
