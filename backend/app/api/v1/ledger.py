import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.ledger import COACreate, COAResponse, JournalEntryCreate, JournalEntryResponse
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.ledger_service import LedgerService
from backend.app.models.ledger import ChartOfAccount, JournalEntry
from backend.app.api.deps import get_current_user, get_tenant_context
from backend.app.models.user import User

router = APIRouter(prefix="/ledger", tags=["Ledger"])

@router.post("/accounts", response_model=ResponseEnvelope[COAResponse], status_code=status.HTTP_201_CREATED)
async def create_coa(
    payload: COACreate,
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    coa = ChartOfAccount(
        organization_id=org_id,
        client_business_id=client_id,
        account_code=payload.account_code,
        account_name=payload.account_name,
        account_type=payload.account_type
    )
    db.add(coa)
    await db.commit()
    await db.refresh(coa)
    return ResponseEnvelope(data=COAResponse.model_validate(coa), message="Account created")

@router.get("/accounts", response_model=ResponseEnvelope[List[COAResponse]])
async def list_coa(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Org header required"})
    query = select(ChartOfAccount).where(ChartOfAccount.organization_id == org_id)
    if client_id:
        query = query.where(ChartOfAccount.client_business_id == client_id)
    res = await db.execute(query)
    return ResponseEnvelope(data=[COAResponse.model_validate(a) for a in res.scalars().all()])

@router.post("/entries", response_model=ResponseEnvelope[JournalEntryResponse], status_code=status.HTTP_201_CREATED)
async def create_entry(
    payload: JournalEntryCreate,
    user: User = Depends(get_current_user),
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    try:
        lines_data = [l.model_dump() for l in payload.lines]
        entry = await LedgerService.post_journal_entry(
            db=db,
            organization_id=org_id,
            client_business_id=client_id,
            user_id=user.id,
            entry_number=payload.entry_number,
            voucher_type=payload.voucher_type,
            narration=payload.narration,
            posting_date=payload.posting_date,
            lines_data=lines_data
        )
        await db.commit()
        await db.refresh(entry, ["lines"])
        return ResponseEnvelope(data=JournalEntryResponse.model_validate(entry), message="Journal entry posted")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "UNBALANCED_ENTRY", "message": str(e)})

@router.get("/trial-balance", response_model=ResponseEnvelope[List[Dict[str, Any]]])
async def get_trial_balance(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    tb = await LedgerService.get_trial_balance(db, org_id, client_id)
    return ResponseEnvelope(data=tb)
