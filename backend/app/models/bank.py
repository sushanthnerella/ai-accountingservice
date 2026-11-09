import uuid
from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import enum

class AccountType(str, enum.Enum):
    CURRENT = "CURRENT"
    SAVINGS = "SAVINGS"
    OVERDRAFT = "OVERDRAFT"
    CREDIT_CARD = "CREDIT_CARD"

class TransactionType(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

class ClassificationCategory(str, enum.Enum):
    OPERATING_REVENUE = "OPERATING_REVENUE"
    OPERATING_EXPENSE = "OPERATING_EXPENSE"
    INTERNAL_CONTRA = "INTERNAL_CONTRA"
    CAPITAL_INJECTION = "CAPITAL_INJECTION"
    OWNER_DRAWINGS = "OWNER_DRAWINGS"
    TAX_PAYMENT_GST = "TAX_PAYMENT_GST"
    TAX_PAYMENT_ADVANCE_TAX = "TAX_PAYMENT_ADVANCE_TAX"
    BANK_CHARGES = "BANK_CHARGES"
    INTEREST_INCOME = "INTEREST_INCOME"
    UNCLASSIFIED = "UNCLASSIFIED"

class ReconciliationStatus(str, enum.Enum):
    UNRECONCILED = "UNRECONCILED"
    PARTIALLY_RECONCILED = "PARTIALLY_RECONCILED"
    FULLY_RECONCILED = "FULLY_RECONCILED"
    EXCLUDED = "EXCLUDED"

class BankAccount(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bank_accounts"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("client_businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    account_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(11), nullable=False)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType, name="account_type_enum"), default=AccountType.CURRENT, nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)
    opening_balance_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_ledger_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0.0000"), nullable=False)

    transactions = relationship("BankTransaction", back_populates="bank_account", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("client_business_id", "account_number", "ifsc_code", name="uq_bank_acc_client_num_ifsc"),
    )

class BankTransaction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "bank_transactions"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("client_businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    bank_account_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)

    transaction_date: Mapped[date] = mapped_column(Date, nullable=False)
    value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    narration: Mapped[str] = mapped_column(Text, nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    utr_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    cheque_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    transaction_type: Mapped[TransactionType] = mapped_column(Enum(TransactionType, name="transaction_type_enum"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    running_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    classification_category: Mapped[ClassificationCategory] = mapped_column(
        Enum(ClassificationCategory, name="classification_category_enum"),
        default=ClassificationCategory.UNCLASSIFIED,
        nullable=False
    )
    reconciliation_status: Mapped[ReconciliationStatus] = mapped_column(
        Enum(ReconciliationStatus, name="reconciliation_status_enum"),
        default=ReconciliationStatus.UNRECONCILED,
        nullable=False
    )
    unreconciled_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    bank_account = relationship("BankAccount", back_populates="transactions")
