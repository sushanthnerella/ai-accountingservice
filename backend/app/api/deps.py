import uuid
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.security import decode_token
from backend.app.core.rls import set_tenant_context
from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.services.organization_service import OrganizationService

security = HTTPBearer(auto_error=False)

async def get_current_user(db: AsyncSession = Depends(get_db), cred: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> User:
    if not cred or not cred.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error_code": "NOT_AUTHENTICATED", "message": "Authentication token missing"})
    try:
        payload = decode_token(cred.credentials)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error_code": "INVALID_TOKEN", "message": str(e)})

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error_code": "INVALID_TOKEN", "message": "Expected access token"})

    user_id = uuid.UUID(payload["sub"])
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error_code": "USER_NOT_FOUND", "message": "User not found or inactive"})
    return user

async def get_tenant_context(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    x_client_business_id: Optional[str] = Header(None, alias="X-Client-Business-Id"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> tuple[Optional[uuid.UUID], Optional[uuid.UUID]]:
    org_id = uuid.UUID(x_organization_id) if x_organization_id else None
    client_id = uuid.UUID(x_client_business_id) if x_client_business_id else None

    if org_id:
        membership = await OrganizationService.get_user_membership(db, user.id, org_id)
        if not membership:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error_code": "FORBIDDEN_TENANT_ACCESS", "message": "Not a member of the requested organization"})
        await set_tenant_context(db, org_id=org_id, client_id=client_id)

    return org_id, client_id
