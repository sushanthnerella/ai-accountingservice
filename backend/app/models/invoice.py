import uuid
from datetime import date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import Boolean, Date, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import enum

class InvoiceType(str, enum.Enum):
    SALES = "SALES"
    PURCHASE = "PURCHASE"
    EXPENSE = "EXPENSE"

class ITCEligibility(str, enum.Enum):
    ELIGIBLE_INPUT_SERVICES = "ELIGIBLE_INPUT_SERVICES"
    ELIGIBLE_INPUT_GOODS = "ELIGIBLE_INPUT_GOODS"
    ELIGIBLE_CAPITAL_GOODS = "ELIGIBLE_CAPITAL_GOODS"
    INELIGIBLE_SEC_17_5 = "INELIGIBLE_SEC_17_5"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"

class ApprovalStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class Invoice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "invoices"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("client_businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    invoice_type: Mapped[InvoiceType] = mapped_column(Enum(InvoiceType, name="invoice_type_enum"), nullable=False)
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    counterparty_name: Mapped[str] = mapped_column(String(255), nullable=False)
    counterparty_gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    counterparty_state_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    place_of_supply_state_code: Mapped[str] = mapped_column(String(2), nullable=False)

    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    cgst_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    sgst_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    igst_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    cess_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    round_off_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    balance_due_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    itc_eligibility: Mapped[ITCEligibility] = mapped_column(Enum(ITCEligibility, name="itc_eligibility_enum"), default=ITCEligibility.PENDING, nullable=False)
    is_reverse_charge: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_export_lut: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lut_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    approval_status: Mapped[ApprovalStatus] = mapped_column(Enum(ApprovalStatus, name="invoice_approval_status_enum"), default=ApprovalStatus.PENDING, nullable=False)

    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("client_business_id", "counterparty_gstin", "invoice_number", name="uq_invoice_client_gstin_num"),
    )

class InvoiceItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "invoice_items"

    invoice_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("1.0000"), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    tax_rate_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("18.00"), nullable=False)

    invoice = relationship("Invoice", back_populates="items")
