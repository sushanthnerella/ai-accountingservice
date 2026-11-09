import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.services.tally_service import TallyService
from backend.app.api.deps import get_tenant_context

router = APIRouter(prefix="/integrations/tally", tags=["TallyPrime Integration"])

@router.get("/export-xml")
async def export_tally_xml(
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Tenant headers required"})

    xml_content = await TallyService.generate_tally_xml(db, org_id, client_id)
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f"attachment; filename=tally_vouchers_{client_id}.xml"}
    )
