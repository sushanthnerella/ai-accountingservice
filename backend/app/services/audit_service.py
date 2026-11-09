import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.audit import AuditEvent, AuditEventType

class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        organization_id: uuid.UUID,
        event_type: AuditEventType,
        entity_name: str,
        entity_id: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        payload_before: Optional[Dict[str, Any]] = None,
        payload_after: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            organization_id=organization_id,
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            entity_name=entity_name,
            entity_id=entity_id,
            payload_before=payload_before,
            payload_after=payload_after,
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    async def get_events_for_org(db: AsyncSession, organization_id: uuid.UUID, skip: int = 0, limit: int = 50) -> List[AuditEvent]:
        query = select(AuditEvent).where(AuditEvent.organization_id == organization_id).order_by(desc(AuditEvent.created_at)).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())
