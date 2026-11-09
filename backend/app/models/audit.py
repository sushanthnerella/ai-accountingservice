import uuid
from typing import Optional
from sqlalchemy import Enum, ForeignKey, String, JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import enum

class AuditEventType(str, enum.Enum):
    USER_REGISTERED = "USER_REGISTERED"
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    ORG_CREATED = "ORG_CREATED"
    CLIENT_CREATED = "CLIENT_CREATED"
    CLIENT_UPDATED = "CLIENT_UPDATED"
    DOC_UPLOADED = "DOC_UPLOADED"
    DOC_DUPLICATE_DETECTED = "DOC_DUPLICATE_DETECTED"
    DOC_PROCESSING_STARTED = "DOC_PROCESSING_STARTED"
    DOC_EXTRACTED = "DOC_EXTRACTED"
    VOUCHER_POSTED = "VOUCHER_POSTED"
    MATCH_ACCEPTED = "MATCH_ACCEPTED"

class AuditEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "audit_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type: Mapped[AuditEventType] = mapped_column(Enum(AuditEventType, name="audit_event_type_enum"), nullable=False, index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entity_name: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    payload_before: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    payload_after: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    organization = relationship("Organization", back_populates="audit_events")
