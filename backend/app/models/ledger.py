import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import enum

class AccountType(str, enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class VoucherType(str, enum.Enum):
    SALES_INVOICE = "SALES_INVOICE"
    PURCHASE_BILL = "PURCHASE_BILL"
    PAYMENT = "PAYMENT"
    RECEIPT = "RECEIPT"
    CONTRA = "CONTRA"
    JOURNAL_ADJUSTMENT = "JOURNAL_ADJUSTMENT"
    REVERSAL = "REVERSAL"

class EntrySide(str, enum.Enum):
    DR = "DR"
    CR = "CR"

class ChartOfAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "chart_of_accounts"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("client_businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    account_code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_name: Mapped[str] = mapped_column(String(150), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType, name="coa_account_type_enum"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    journal_lines = relationship("JournalLine", back_populates="account")

    __table_args__ = (
        UniqueConstraint("client_business_id", "account_code", name="uq_coa_code_client"),
    )

class JournalEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "journal_entries"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("client_businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_number: Mapped[str] = mapped_column(String(50), nullable=False)
    posting_date: Mapped[date] = mapped_column(Date, nullable=False)
    financial_year: Mapped[str] = mapped_column(String(9), default="2024-2025", nullable=False)
    voucher_type: Mapped[VoucherType] = mapped_column(Enum(VoucherType, name="voucher_type_enum"), nullable=False)
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    lines = relationship("JournalLine", back_populates="journal_entry", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("client_business_id", "financial_year", "entry_number", name="uq_entry_num_fy_client"),
    )

class JournalLine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "journal_lines"

    journal_entry_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("chart_of_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    entry_side: Mapped[EntrySide] = mapped_column(Enum(EntrySide, name="entry_side_enum"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    journal_entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("ChartOfAccount", back_populates="journal_lines")
