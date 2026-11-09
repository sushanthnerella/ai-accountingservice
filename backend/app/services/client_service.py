import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.client_business import ClientBusiness, BusinessType
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService

class ClientService:
    @staticmethod
    async def create_client_business(db: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID, legal_name: str, pan: str, state_code: str, trade_name: str = None, business_type: BusinessType = BusinessType.PROPRIETORSHIP, gstin: str = None, is_composition_scheme: bool = False) -> ClientBusiness:
        stmt = select(ClientBusiness).where(ClientBusiness.organization_id == organization_id, ClientBusiness.pan == pan)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise ValueError(f"Client Business with PAN '{pan}' already exists in this organization")

        client = ClientBusiness(
            organization_id=organization_id,
            legal_name=legal_name,
            trade_name=trade_name,
            business_type=business_type,
            pan=pan,
            gstin=gstin,
            state_code=state_code,
            is_composition_scheme=is_composition_scheme,
            is_active=True
        )
        db.add(client)
        await db.flush()

        await AuditService.log_event(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            event_type=AuditEventType.CLIENT_CREATED,
            entity_name="ClientBusiness",
            entity_id=str(client.id),
            payload_after={"legal_name": legal_name, "pan": pan, "gstin": gstin}
        )
        return client

    @staticmethod
    async def get_client_businesses(db: AsyncSession, organization_id: uuid.UUID) -> List[ClientBusiness]:
        query = select(ClientBusiness).where(ClientBusiness.organization_id == organization_id, ClientBusiness.is_active == True)
        res = await db.execute(query)
        return list(res.scalars().all())

    @staticmethod
    async def get_client_by_id(db: AsyncSession, organization_id: uuid.UUID, client_id: uuid.UUID) -> Optional[ClientBusiness]:
        query = select(ClientBusiness).where(ClientBusiness.organization_id == organization_id, ClientBusiness.id == client_id, ClientBusiness.is_active == True)
        res = await db.execute(query)
        return res.scalar_one_or_none()
