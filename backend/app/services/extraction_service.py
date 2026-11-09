import uuid
from decimal import Decimal
from datetime import date
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.invoice import Invoice, InvoiceItem, InvoiceType, ITCEligibility, ApprovalStatus
from backend.app.models.document import Document, DocumentStatus

class ExtractionService:
    @staticmethod
    def validate_arithmetic_invariants(
        taxable_amount: Decimal,
        cgst_amount: Decimal,
        sgst_amount: Decimal,
        igst_amount: Decimal,
        cess_amount: Decimal,
        round_off_amount: Decimal,
        total_amount: Decimal
    ) -> bool:
        """
        Inviolable Invariant:
        Taxable + CGST + SGST + IGST + Cess + RoundOff == Total ± 0.05 tolerance
        """
        calculated_total = taxable_amount + cgst_amount + sgst_amount + igst_amount + cess_amount + round_off_amount
        return abs(calculated_total - total_amount) <= Decimal("0.0500")

    @staticmethod
    async def extract_and_stage_invoice(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID,
        document: Document,
        raw_extraction: Dict[str, Any]
    ) -> Invoice:
        taxable = Decimal(str(raw_extraction.get("taxable_amount", "0.0000")))
        cgst = Decimal(str(raw_extraction.get("cgst_amount", "0.0000")))
        sgst = Decimal(str(raw_extraction.get("sgst_amount", "0.0000")))
        igst = Decimal(str(raw_extraction.get("igst_amount", "0.0000")))
        cess = Decimal(str(raw_extraction.get("cess_amount", "0.0000")))
        round_off = Decimal(str(raw_extraction.get("round_off_amount", "0.0000")))
        total = Decimal(str(raw_extraction.get("total_amount", "0.0000")))

        # Check invariant
        is_balanced = ExtractionService.validate_arithmetic_invariants(
            taxable, cgst, sgst, igst, cess, round_off, total
        )
        if not is_balanced:
            document.status = DocumentStatus.REVIEW_PENDING
        else:
            document.status = DocumentStatus.EXTRACTED

        invoice = Invoice(
            organization_id=organization_id,
            client_business_id=client_business_id,
            document_id=document.id,
            invoice_type=InvoiceType(raw_extraction.get("invoice_type", "PURCHASE")),
            invoice_number=raw_extraction.get("invoice_number", f"INV-{uuid.uuid4().hex[:8]}"),
            invoice_date=raw_extraction.get("invoice_date", date.today()),
            due_date=raw_extraction.get("due_date"),
            counterparty_name=raw_extraction.get("counterparty_name", "Vendor Partner"),
            counterparty_gstin=raw_extraction.get("counterparty_gstin"),
            counterparty_state_code=raw_extraction.get("counterparty_state_code"),
            place_of_supply_state_code=raw_extraction.get("place_of_supply_state_code", "27"),
            taxable_amount=taxable,
            cgst_amount=cgst,
            sgst_amount=sgst,
            igst_amount=igst,
            cess_amount=cess,
            round_off_amount=round_off,
            total_amount=total,
            balance_due_amount=total,
            currency="INR",
            itc_eligibility=ITCEligibility.PENDING,
            approval_status=ApprovalStatus.PENDING
        )
        db.add(invoice)
        await db.flush()

        # Add line items if present
        for item in raw_extraction.get("items", []):
            inv_item = InvoiceItem(
                invoice_id=invoice.id,
                description=item.get("description", "Standard Supply"),
                hsn_sac_code=item.get("hsn_sac_code", "9983"),
                quantity=Decimal(str(item.get("quantity", "1.0000"))),
                unit_price=Decimal(str(item.get("unit_price", taxable))),
                taxable_amount=Decimal(str(item.get("taxable_amount", taxable))),
                tax_rate_percent=Decimal(str(item.get("tax_rate_percent", "18.00")))
            )
            db.add(inv_item)

        await db.flush()
        return invoice
