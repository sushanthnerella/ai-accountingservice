import uuid
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.zoho_service import ZohoService
from backend.app.api.deps import get_tenant_context

router = APIRouter(prefix="/integrations/zoho", tags=["Zoho Books Integration"])

@router.post("/sync", response_model=ResponseEnvelope[Dict[str, Any]])
async def sync_zoho(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    result = await ZohoService.sync_approved_invoices(db, org_id, client_id)
    return ResponseEnvelope(data=result, message="Zoho Books sync complete")
