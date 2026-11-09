import uuid
from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import enum

class OrganizationType(str, enum.Enum):
    FREELANCER = "FREELANCER"
    CA_FIRM = "CA_FIRM"
    ENTERPRISE = "ENTERPRISE"

class MemberRole(str, enum.Enum):
    FIRM_ADMIN = "FIRM_ADMIN"
    SENIOR_CA = "SENIOR_CA"
    STAFF_ACCOUNTANT = "STAFF_ACCOUNTANT"
    CLIENT_VIEWER = "CLIENT_VIEWER"
    AUDITOR = "AUDITOR"

class Organization(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    org_type: Mapped[OrganizationType] = mapped_column(
        Enum(OrganizationType, name="org_type_enum"),
        default=OrganizationType.FREELANCER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    memberships = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")
    client_businesses = relationship("ClientBusiness", back_populates="organization", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="organization", cascade="all, delete-orphan")

class OrganizationMembership(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "organization_memberships"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[MemberRole] = mapped_column(Enum(MemberRole, name="member_role_enum"), default=MemberRole.STAFF_ACCOUNTANT, nullable=False)

    organization = relationship("Organization", back_populates="memberships")
    user = relationship("User", back_populates="memberships")

    __table_args__ = (UniqueConstraint("organization_id", "user_id", name="uq_org_member"),)
