import uuid
import hashlib
from typing import List, Tuple, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.document import Document, DocumentBatch, BatchStatus, DocumentStatus, DocumentCategory
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService
from backend.app.services.storage_service import StorageService, get_storage_service

class DocumentService:
    @staticmethod
    def validate_file_signature(content: bytes, filename: str) -> str:
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        if content.startswith(b"%PDF-"):
            return "application/pdf"
        elif content.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif content.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        elif content.startswith(b"PK\x03\x04"):
            return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if ext in ["xlsx", "xls"] else "application/zip"
        if ext in ["csv", "txt"]:
            return "text/csv"
        raise ValueError(f"Unsupported file type or invalid signature for file: {filename}")

    @staticmethod
    def calculate_sha256(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    async def process_upload_batch(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID,
        user_id: uuid.UUID,
        files: List[Tuple[str, bytes]],
        category: DocumentCategory = DocumentCategory.AUTO_DETECT,
        storage_service: Optional[StorageService] = None
    ) -> DocumentBatch:
        storage = storage_service or get_storage_service()
        batch_ref = f"bch_{uuid.uuid4().hex[:12]}"
        batch = DocumentBatch(
            organization_id=organization_id,
            client_business_id=client_business_id,
            batch_reference=batch_ref,
            total_files=len(files),
            status=BatchStatus.PROCESSING
        )
        db.add(batch)
        await db.flush()

        for filename, content in files:
            mime_type = DocumentService.validate_file_signature(content, filename)
            sha256 = DocumentService.calculate_sha256(content)
            file_size = len(content)

            dup_query = select(Document).where(
                Document.organization_id == organization_id,
                Document.client_business_id == client_business_id,
                Document.sha256_hash == sha256
            )
            dup_res = await db.execute(dup_query)
            existing_doc = dup_res.scalars().first()

            is_duplicate = existing_doc is not None
            duplicate_of_id = existing_doc.id if existing_doc else None

            storage_path = f"org_{organization_id}/client_{client_business_id}/{batch_ref}/{sha256}_{filename}"
            if not is_duplicate:
                await storage.save_file(content, storage_path)
            else:
                storage_path = existing_doc.storage_path

            doc = Document(
                organization_id=organization_id,
                client_business_id=client_business_id,
                batch_id=batch.id,
                original_filename=filename,
                file_size_bytes=file_size,
                mime_type=mime_type,
                sha256_hash=sha256,
                storage_path=storage_path,
                category=category,
                status=DocumentStatus.UPLOADED if is_duplicate else DocumentStatus.PROCESSING,
                is_duplicate=is_duplicate,
                duplicate_of_id=duplicate_of_id,
                metadata_json={"batch_ref": batch_ref}
            )
            db.add(doc)
            await db.flush()

            await AuditService.log_event(
                db=db,
                organization_id=organization_id,
                user_id=user_id,
                event_type=AuditEventType.DOC_DUPLICATE_DETECTED if is_duplicate else AuditEventType.DOC_UPLOADED,
                entity_name="Document",
                entity_id=str(doc.id),
                payload_after={"filename": filename, "sha256": sha256, "is_duplicate": is_duplicate, "batch_id": str(batch.id)}
            )

        return batch
