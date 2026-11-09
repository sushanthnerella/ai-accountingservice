import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.invoice import InvoiceCreate, InvoiceResponse
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.extraction_service import ExtractionService
from backend.app.models.invoice import Invoice, ApprovalStatus
from backend.app.api.deps import get_current_user, get_tenant_context
from backend.app.models.user import User

router = APIRouter(prefix="/invoices", tags=["Invoices"])

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
    res = await db.execute(query)
    return ResponseEnvelope(data=[InvoiceResponse.model_validate(inv) for inv in res.scalars().all()])
