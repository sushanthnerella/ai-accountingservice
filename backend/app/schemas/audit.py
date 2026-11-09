import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.audit import AuditEventType

class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    event_type: AuditEventType
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    entity_name: str
    entity_id: Optional[str] = None
    payload_before: Optional[Dict[str, Any]] = None
    payload_after: Optional[Dict[str, Any]] = None
    created_at: datetime
