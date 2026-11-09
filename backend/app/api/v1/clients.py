import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.client_business import ClientBusinessCreateRequest, ClientBusinessResponse
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.client_service import ClientService
from backend.app.api.deps import get_current_user, get_tenant_context
from backend.app.models.user import User

router = APIRouter(prefix="/clients", tags=["Client Businesses"])

@router.post("", response_model=ResponseEnvelope[ClientBusinessResponse], status_code=status.HTTP_201_CREATED)
async def create_client(request: ClientBusinessCreateRequest, user: User = Depends(get_current_user), tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    org_id, _ = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "X-Organization-Id header is required"})
    try:
        client = await ClientService.create_client_business(
            db=db,
            organization_id=org_id,
            user_id=user.id,
            legal_name=request.legal_name,
            trade_name=request.trade_name,
            business_type=request.business_type,
            pan=request.pan,
            gstin=request.gstin,
            state_code=request.state_code,
            is_composition_scheme=request.is_composition_scheme
        )
        await db.commit()
        await db.refresh(client)
        return ResponseEnvelope(data=ClientBusinessResponse.model_validate(client), message="Client business created")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "CLIENT_CREATION_FAILED", "message": str(e)})

@router.get("", response_model=ResponseEnvelope[List[ClientBusinessResponse]])
async def list_clients(tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    org_id, _ = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "X-Organization-Id header is required"})
    clients = await ClientService.get_client_businesses(db, org_id)
    return ResponseEnvelope(data=[ClientBusinessResponse.model_validate(c) for c in clients])

@router.get("/{client_id}", response_model=ResponseEnvelope[ClientBusinessResponse])
async def get_client(client_id: uuid.UUID, tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    org_id, _ = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "X-Organization-Id header is required"})
    client = await ClientService.get_client_by_id(db, org_id, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error_code": "CLIENT_NOT_FOUND", "message": "Client business not found"})
    return ResponseEnvelope(data=ClientBusinessResponse.model_validate(client))
