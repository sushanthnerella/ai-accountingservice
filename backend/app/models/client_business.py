import uuid
from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import enum

class BusinessType(str, enum.Enum):
    PROPRIETORSHIP = "PROPRIETORSHIP"
    INDIVIDUAL = "INDIVIDUAL"
    PARTNERSHIP = "PARTNERSHIP"
    LLP = "LLP"
    PVT_LTD = "PVT_LTD"
    OTHER = "OTHER"

class ClientBusiness(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "client_businesses"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    trade_name: Mapped[str] = mapped_column(String(255), nullable=True)
    business_type: Mapped[BusinessType] = mapped_column(Enum(BusinessType, name="business_type_enum"), default=BusinessType.PROPRIETORSHIP, nullable=False)
    pan: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    gstin: Mapped[str] = mapped_column(String(15), nullable=True, index=True)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    is_composition_scheme: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization = relationship("Organization", back_populates="client_businesses")
    document_batches = relationship("DocumentBatch", back_populates="client_business", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="client_business", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("organization_id", "pan", name="uq_org_pan"),)
