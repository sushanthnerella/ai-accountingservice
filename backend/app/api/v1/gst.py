import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.gst_service import GSTService
from backend.app.api.deps import get_tenant_context

router = APIRouter(prefix="/gst", tags=["GST Intelligence"])

@router.get("/gstr-3b-summary", response_model=ResponseEnvelope[Dict[str, Any]])
async def get_gstr_3b_summary(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    summary = await GSTService.compute_gstr_3b_summary(db, org_id, client_id)
    return ResponseEnvelope(data=summary)
