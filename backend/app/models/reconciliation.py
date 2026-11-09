import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import enum

class MatchScenario(str, enum.Enum):
    EXACT_ONE_TO_ONE = "EXACT_ONE_TO_ONE"
    ONE_TO_MANY_INVOICES = "ONE_TO_MANY_INVOICES"
    MANY_TRANSACTIONS_ONE_INVOICE = "MANY_TRANSACTIONS_ONE_INVOICE"
    PARTIAL_PAYMENT = "PARTIAL_PAYMENT"
    ADVANCE_PAYMENT = "ADVANCE_PAYMENT"
    TDS_ADJUSTED_SETTLEMENT = "TDS_ADJUSTED_SETTLEMENT"
    CONTRA_TRANSFER = "CONTRA_TRANSFER"
    MANUAL_ALLOCATION = "MANUAL_ALLOCATION"

class TDSSection(str, enum.Enum):
    SEC_194C = "194C"
    SEC_194J_TECH = "194J_TECH"  # 2%
    SEC_194J_PROF = "194J_PROF"  # 10%
    NONE = "NONE"

class MatchApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class ReconciliationMatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reconciliation_matches"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("client_businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_transaction_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("bank_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True, index=True)

    match_scenario: Mapped[MatchScenario] = mapped_column(Enum(MatchScenario, name="match_scenario_enum"), nullable=False)
    allocated_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    tds_deducted_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    tds_section: Mapped[TDSSection] = mapped_column(Enum(TDSSection, name="tds_section_enum"), default=TDSSection.NONE, nullable=False)
    confidence_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    match_rationale: Mapped[str] = mapped_column(Text, nullable=False)

    approval_status: Mapped[MatchApprovalStatus] = mapped_column(
        Enum(MatchApprovalStatus, name="match_approval_status_enum"),
        default=MatchApprovalStatus.PENDING,
        nullable=False
    )
    approved_by_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
