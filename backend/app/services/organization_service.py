import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.organization import Organization, OrganizationMembership, OrganizationType, MemberRole
from backend.app.models.user import User
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService

class OrganizationService:
    @staticmethod
    async def create_organization(db: AsyncSession, user: User, name: str, slug: str, org_type: OrganizationType = OrganizationType.FREELANCER) -> Organization:
        stmt = select(Organization).where(Organization.slug == slug.lower())
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ValueError(f"Organization with slug '{slug}' already exists")

        org = Organization(name=name, slug=slug.lower(), org_type=org_type, is_active=True)
        db.add(org)
        await db.flush()

        membership = OrganizationMembership(organization_id=org.id, user_id=user.id, role=MemberRole.FIRM_ADMIN)
        db.add(membership)
        await db.flush()

        await AuditService.log_event(
            db=db,
            organization_id=org.id,
            user_id=user.id,
            event_type=AuditEventType.ORG_CREATED,
            entity_name="Organization",
            entity_id=str(org.id),
            payload_after={"name": name, "slug": slug, "type": org_type.value}
        )
        return org

    @staticmethod
    async def get_user_organizations(db: AsyncSession, user_id: uuid.UUID) -> List[tuple[Organization, MemberRole]]:
        query = select(Organization, OrganizationMembership.role).join(OrganizationMembership, Organization.id == OrganizationMembership.organization_id).where(OrganizationMembership.user_id == user_id, Organization.is_active == True)
        result = await db.execute(query)
        return [(row[0], row[1]) for row in result.all()]

    @staticmethod
    async def get_user_membership(db: AsyncSession, user_id: uuid.UUID, org_id: uuid.UUID) -> Optional[OrganizationMembership]:
        query = select(OrganizationMembership).where(OrganizationMembership.user_id == user_id, OrganizationMembership.organization_id == org_id)
        res = await db.execute(query)
        return res.scalar_one_or_none()
