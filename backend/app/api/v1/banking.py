import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.bank import BankAccountCreate, BankAccountResponse, BankTransactionResponse
from backend.app.schemas.common import ResponseEnvelope
from backend.app.models.bank import BankAccount, BankTransaction
from backend.app.api.deps import get_tenant_context

router = APIRouter(prefix="/banking", tags=["Banking"])

@router.post("/accounts", response_model=ResponseEnvelope[BankAccountResponse], status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    payload: BankAccountCreate,
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    acc = BankAccount(
        organization_id=org_id,
        client_business_id=client_id,
        account_name=payload.account_name,
        account_number=payload.account_number,
        ifsc_code=payload.ifsc_code,
        bank_name=payload.bank_name,
        account_type=payload.account_type,
        opening_balance=payload.opening_balance,
        opening_balance_date=payload.opening_balance_date,
        current_ledger_balance=payload.opening_balance
    )
    db.add(acc)
    await db.commit()
    await db.refresh(acc)
    return ResponseEnvelope(data=BankAccountResponse.model_validate(acc), message="Bank account created")

@router.get("/accounts", response_model=ResponseEnvelope[List[BankAccountResponse]])
async def list_bank_accounts(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Org header required"})
    query = select(BankAccount).where(BankAccount.organization_id == org_id)
    if client_id:
        query = query.where(BankAccount.client_business_id == client_id)
    res = await db.execute(query)
    return ResponseEnvelope(data=[BankAccountResponse.model_validate(a) for a in res.scalars().all()])

@router.get("/transactions", response_model=ResponseEnvelope[List[BankTransactionResponse]])
async def list_bank_transactions(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Org header required"})
    query = select(BankTransaction).where(BankTransaction.organization_id == org_id)
    if client_id:
        query = query.where(BankTransaction.client_business_id == client_id)
    res = await db.execute(query)
    return ResponseEnvelope(data=[BankTransactionResponse.model_validate(t) for t in res.scalars().all()])
