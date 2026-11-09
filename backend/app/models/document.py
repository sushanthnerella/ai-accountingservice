import uuid
from typing import Optional
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
import enum

class BatchStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DocumentStatus(str, enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    EXTRACTED = "EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"
    MATCHED = "MATCHED"
    UNMATCHED = "UNMATCHED"
    REVIEW_PENDING = "REVIEW_PENDING"
    APPROVED = "APPROVED"
    POSTED = "POSTED"

class DocumentCategory(str, enum.Enum):
    SALES_INVOICE = "SALES_INVOICE"
    PURCHASE_INVOICE = "PURCHASE_INVOICE"
    EXPENSE_RECEIPT = "EXPENSE_RECEIPT"
    BANK_STATEMENT = "BANK_STATEMENT"
    CREDIT_DEBIT_NOTE = "CREDIT_DEBIT_NOTE"
    AUTO_DETECT = "AUTO_DETECT"

class DocumentBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "document_batches"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("client_businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_reference: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    total_files: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus, name="batch_status_enum"), default=BatchStatus.PROCESSING, nullable=False)

    client_business = relationship("ClientBusiness", back_populates="document_batches")
    documents = relationship("Document", back_populates="batch", cascade="all, delete-orphan")

class Document(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "documents"

    organization_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    client_business_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("client_businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("document_batches.id", ondelete="SET NULL"), nullable=True, index=True)

    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[DocumentCategory] = mapped_column(Enum(DocumentCategory, name="document_category_enum"), default=DocumentCategory.AUTO_DETECT, nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus, name="document_status_enum"), default=DocumentStatus.PROCESSING, nullable=False)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_id: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    batch = relationship("DocumentBatch", back_populates="documents")
    client_business = relationship("ClientBusiness", back_populates="documents")

    __table_args__ = (
        Index("idx_docs_org_client_sha", "organization_id", "client_business_id", "sha256_hash"),
    )
