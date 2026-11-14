import uuid
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.invoice import InvoiceCreate, InvoiceResponse
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.ledger_service import LedgerService
from backend.app.models.invoice import Invoice, InvoiceType, ApprovalStatus
from backend.app.models.ledger import ChartOfAccount, AccountType, VoucherType
from backend.app.api.deps import get_current_user, get_tenant_context
from backend.app.models.user import User

router = APIRouter(prefix="/invoices", tags=["Invoices"])

async def _get_or_create_account(
    db: AsyncSession,
    organization_id: uuid.UUID,
    client_business_id: uuid.UUID,
    code: str,
    name: str,
    account_type: AccountType
) -> ChartOfAccount:
    q = select(ChartOfAccount).where(
        ChartOfAccount.client_business_id == client_business_id,
        ChartOfAccount.account_code == code
    )
    acc = (await db.execute(q)).scalar_one_or_none()
    if not acc:
        acc = ChartOfAccount(
            organization_id=organization_id,
            client_business_id=client_business_id,
            account_code=code,
            account_name=name,
            account_type=account_type
        )
        db.add(acc)
        await db.flush()
    return acc

@router.post("", response_model=ResponseEnvelope[InvoiceResponse], status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    invoice = Invoice(
        organization_id=org_id,
        client_business_id=client_id,
        document_id=payload.document_id,
        invoice_type=payload.invoice_type,
        invoice_number=payload.invoice_number,
        invoice_date=payload.invoice_date,
        due_date=payload.due_date,
        counterparty_name=payload.counterparty_name,
        counterparty_gstin=payload.counterparty_gstin,
        place_of_supply_state_code=payload.place_of_supply_state_code,
        taxable_amount=payload.taxable_amount,
        cgst_amount=payload.cgst_amount,
        sgst_amount=payload.sgst_amount,
        igst_amount=payload.igst_amount,
        cess_amount=payload.cess_amount,
        round_off_amount=payload.round_off_amount,
        total_amount=payload.total_amount,
        balance_due_amount=payload.total_amount,
        currency="INR",
        itc_eligibility=payload.itc_eligibility,
        is_reverse_charge=payload.is_reverse_charge,
        is_export_lut=payload.is_export_lut,
        lut_number=payload.lut_number,
        approval_status=ApprovalStatus.PENDING
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    return ResponseEnvelope(data=InvoiceResponse.model_validate(invoice), message="Invoice created")

@router.get("", response_model=ResponseEnvelope[List[InvoiceResponse]])
async def list_invoices(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Org header required"})
    query = select(Invoice).where(Invoice.organization_id == org_id)
    if client_id:
        query = query.where(Invoice.client_business_id == client_id)
    query = query.order_by(Invoice.created_at.desc())
    res = await db.execute(query)
    return ResponseEnvelope(data=[InvoiceResponse.model_validate(inv) for inv in res.scalars().all()])

@router.post("/{invoice_id}/approve", response_model=ResponseEnvelope[InvoiceResponse])
async def approve_invoice(
    invoice_id: uuid.UUID,
    user: User = Depends(get_current_user),
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    invoice = await db.get(Invoice, invoice_id)
    if not invoice or invoice.organization_id != org_id or invoice.client_business_id != client_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": "NOT_FOUND", "message": "Invoice not found"})

    if invoice.approval_status == ApprovalStatus.APPROVED:
        return ResponseEnvelope(data=InvoiceResponse.model_validate(invoice), message="Invoice already approved")

    # Post balanced journal entry into General Ledger
    lines_data = []
    if invoice.invoice_type in (InvoiceType.PURCHASE, InvoiceType.EXPENSE):
        acc_exp = await _get_or_create_account(db, org_id, client_id, "5001", "Operating Expense", AccountType.EXPENSE)
        acc_ap = await _get_or_create_account(db, org_id, client_id, "2001", "Accounts Payable", AccountType.LIABILITY)
        lines_data.append({"account_id": acc_exp.id, "entry_side": "DR", "amount": invoice.taxable_amount, "description": f"Expense {invoice.invoice_number}"})

        if invoice.cgst_amount > Decimal("0.00"):
            acc_cgst = await _get_or_create_account(db, org_id, client_id, "1003", "Input CGST", AccountType.ASSET)
            lines_data.append({"account_id": acc_cgst.id, "entry_side": "DR", "amount": invoice.cgst_amount, "description": "Input CGST"})
        if invoice.sgst_amount > Decimal("0.00"):
            acc_sgst = await _get_or_create_account(db, org_id, client_id, "1004", "Input SGST", AccountType.ASSET)
            lines_data.append({"account_id": acc_sgst.id, "entry_side": "DR", "amount": invoice.sgst_amount, "description": "Input SGST"})
        if invoice.igst_amount > Decimal("0.00"):
            acc_igst = await _get_or_create_account(db, org_id, client_id, "1005", "Input IGST", AccountType.ASSET)
            lines_data.append({"account_id": acc_igst.id, "entry_side": "DR", "amount": invoice.igst_amount, "description": "Input IGST"})

        if invoice.round_off_amount != Decimal("0.00"):
            acc_ro = await _get_or_create_account(db, org_id, client_id, "5002", "Round Off Adjustment", AccountType.EXPENSE)
            side = "DR" if invoice.round_off_amount > 0 else "CR"
            lines_data.append({"account_id": acc_ro.id, "entry_side": side, "amount": abs(invoice.round_off_amount), "description": "Round off"})

        lines_data.append({"account_id": acc_ap.id, "entry_side": "CR", "amount": invoice.total_amount, "description": f"Bill Payable #{invoice.invoice_number}"})
        v_type = VoucherType.PURCHASE_BILL
    else:
        acc_ar = await _get_or_create_account(db, org_id, client_id, "1002", "Accounts Receivable", AccountType.ASSET)
        acc_rev = await _get_or_create_account(db, org_id, client_id, "4001", "Operating Revenue", AccountType.INCOME)
        lines_data.append({"account_id": acc_ar.id, "entry_side": "DR", "amount": invoice.total_amount, "description": f"Receivable #{invoice.invoice_number}"})
        lines_data.append({"account_id": acc_rev.id, "entry_side": "CR", "amount": invoice.taxable_amount, "description": f"Revenue {invoice.invoice_number}"})

        if invoice.cgst_amount > Decimal("0.00"):
            acc_cgst = await _get_or_create_account(db, org_id, client_id, "2002", "Output CGST", AccountType.LIABILITY)
            lines_data.append({"account_id": acc_cgst.id, "entry_side": "CR", "amount": invoice.cgst_amount, "description": "Output CGST"})
        if invoice.sgst_amount > Decimal("0.00"):
            acc_sgst = await _get_or_create_account(db, org_id, client_id, "2003", "Output SGST", AccountType.LIABILITY)
            lines_data.append({"account_id": acc_sgst.id, "entry_side": "CR", "amount": invoice.sgst_amount, "description": "Output SGST"})
        if invoice.igst_amount > Decimal("0.00"):
            acc_igst = await _get_or_create_account(db, org_id, client_id, "2004", "Output IGST", AccountType.LIABILITY)
            lines_data.append({"account_id": acc_igst.id, "entry_side": "CR", "amount": invoice.igst_amount, "description": "Output IGST"})

        if invoice.round_off_amount != Decimal("0.00"):
            acc_ro = await _get_or_create_account(db, org_id, client_id, "5002", "Round Off Adjustment", AccountType.EXPENSE)
            side = "CR" if invoice.round_off_amount > 0 else "DR"
            lines_data.append({"account_id": acc_ro.id, "entry_side": side, "amount": abs(invoice.round_off_amount), "description": "Round off"})

        v_type = VoucherType.SALES_INVOICE

    await LedgerService.post_journal_entry(
        db=db,
        organization_id=org_id,
        client_business_id=client_id,
        user_id=user.id,
        entry_number=f"INV-{invoice.invoice_number}-{uuid.uuid4().hex[:4]}",
        voucher_type=v_type,
        narration=f"Voucher posted on approval of {invoice.invoice_type.value} #{invoice.invoice_number}",
        posting_date=invoice.invoice_date,
        lines_data=lines_data
    )

    invoice.approval_status = ApprovalStatus.APPROVED
    await db.commit()
    await db.refresh(invoice)
    return ResponseEnvelope(data=InvoiceResponse.model_validate(invoice), message="Invoice approved and posted to general ledger")
