from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.organization import OrganizationCreateRequest, OrganizationResponse
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.organization_service import OrganizationService
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.post("", response_model=ResponseEnvelope[OrganizationResponse], status_code=status.HTTP_201_CREATED)
async def create_organization(request: OrganizationCreateRequest, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        org = await OrganizationService.create_organization(db=db, user=user, name=request.name, slug=request.slug, org_type=request.org_type)
        await db.commit()
        await db.refresh(org)
        return ResponseEnvelope(data=OrganizationResponse.model_validate(org), message="Organization created successfully")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "ORG_CREATION_FAILED", "message": str(e)})

@router.get("", response_model=ResponseEnvelope[List[OrganizationResponse]])
async def list_organizations(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_tuples = await OrganizationService.get_user_organizations(db, user.id)
    result = []
    for org, role in org_tuples:
        org_data = OrganizationResponse.model_validate(org)
        org_data.user_role = role
        result.append(org_data)
    return ResponseEnvelope(data=result)
