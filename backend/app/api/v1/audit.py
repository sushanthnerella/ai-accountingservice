import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.audit import AuditEventResponse
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.audit_service import AuditService
from backend.app.api.deps import get_tenant_context

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("", response_model=ResponseEnvelope[List[AuditEventResponse]])
async def list_audit_events(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    org_id, _ = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "X-Organization-Id header is required"})
    events = await AuditService.get_events_for_org(db, org_id, skip=skip, limit=limit)
    return ResponseEnvelope(data=[AuditEventResponse.model_validate(e) for e in events])
