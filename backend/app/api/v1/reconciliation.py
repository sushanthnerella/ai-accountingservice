import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.reconciliation import MatchApprovalRequest, ReconciliationMatchResponse
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.reconciliation_service import ReconciliationService
from backend.app.models.reconciliation import ReconciliationMatch, MatchApprovalStatus
from backend.app.api.deps import get_current_user, get_tenant_context
from backend.app.models.user import User

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])

@router.post("/propose", response_model=ResponseEnvelope[List[ReconciliationMatchResponse]])
async def propose_matches(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    matches = await ReconciliationService.generate_match_candidates(db, org_id, client_id)
    await db.commit()
    return ResponseEnvelope(data=[ReconciliationMatchResponse.model_validate(m) for m in matches], message="Matches proposed")

@router.get("/matches", response_model=ResponseEnvelope[List[ReconciliationMatchResponse]])
async def list_matches(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Org header required"})
    query = select(ReconciliationMatch).where(ReconciliationMatch.organization_id == org_id)
    if client_id:
        query = query.where(ReconciliationMatch.client_business_id == client_id)
    res = await db.execute(query)
    return ResponseEnvelope(data=[ReconciliationMatchResponse.model_validate(m) for m in res.scalars().all()])

@router.post("/matches/{match_id}/approve", response_model=ResponseEnvelope[ReconciliationMatchResponse])
async def approve_match(
    match_id: uuid.UUID,
    payload: MatchApprovalRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        is_approved = payload.approval_status == MatchApprovalStatus.APPROVED
        match = await ReconciliationService.approve_match(
            db=db,
            match_id=match_id,
            user_id=user.id,
            approved=is_approved,
            rejection_reason=payload.rejection_reason
        )
        await db.commit()
        await db.refresh(match)
        return ResponseEnvelope(data=ReconciliationMatchResponse.model_validate(match), message="Match approval status updated")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": "MATCH_NOT_FOUND", "message": str(e)})
