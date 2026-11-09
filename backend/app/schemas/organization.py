import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from backend.app.models.organization import OrganizationType, MemberRole

class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    org_type: OrganizationType = OrganizationType.FREELANCER

class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    org_type: OrganizationType
    is_active: bool
    created_at: datetime
    user_role: Optional[MemberRole] = None
