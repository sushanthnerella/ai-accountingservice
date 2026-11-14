import asyncio
import logging
import uuid
from typing import Dict, Any
from sqlalchemy import select
from backend.app.tasks.celery_app import celery_app
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.document import Document, DocumentBatch, DocumentStatus
from backend.app.models.client_business import ClientBusiness
from backend.app.services.storage_service import get_storage_service
from backend.app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)

async def process_document_batch_async(batch_id_str: str, organization_id_str: str, client_id_str: str) -> Dict[str, Any]:
    batch_id = uuid.UUID(batch_id_str)
    org_id = uuid.UUID(organization_id_str)
    client_id = uuid.UUID(client_id_str)

    storage = get_storage_service()

    async with AsyncSessionLocal() as session:
        # Fetch client business to retrieve client GSTIN
        client = await session.get(ClientBusiness, client_id)
        client_gstin = client.gstin if client else None

        # Fetch documents in batch
        q = select(Document).where(
            Document.batch_id == batch_id,
            Document.organization_id == org_id,
            Document.client_business_id == client_id
        )
        docs = (await session.execute(q)).scalars().all()

        processed_count = 0
        for doc in docs:
            if doc.status not in (DocumentStatus.UPLOADED, DocumentStatus.PROCESSING):
                continue
            doc.status = DocumentStatus.PROCESSING
            await session.flush()

            try:
                # Read document bytes
                file_bytes = await storage.read_file(doc.storage_path)
                # Run real LLM or high-precision fallback extraction
                extracted_data = await ExtractionService.extract_via_llm_or_ocr(
                    file_content=file_bytes,
                    filename=doc.original_filename,
                    mime_type=doc.mime_type,
                    client_gstin=client_gstin
                )

                # Stage invoice and validate arithmetic invariants
                await ExtractionService.extract_and_stage_invoice(
                    db=session,
                    organization_id=org_id,
                    client_business_id=client_id,
                    document=doc,
                    raw_extraction=extracted_data.model_dump()
                )
                processed_count += 1
            except Exception as e:
                logger.error(f"Error extracting document {doc.id} ({doc.original_filename}): {e}", exc_info=True)
                doc.status = DocumentStatus.PROCESSING_FAILED

        await session.commit()
        logger.info(f"Successfully processed {processed_count} documents for batch {batch_id}")
        return {"batch_id": batch_id_str, "status": "COMPLETED", "processed_count": processed_count}

@celery_app.task(name="tasks.process_document_batch", bind=True, max_retries=3)
def process_document_batch_task(self, batch_id: str, organization_id: str, client_id: str):
    logger.info(f"Celery processing batch {batch_id} for org {organization_id}, client {client_id}")
    try:
        return asyncio.run(process_document_batch_async(batch_id, organization_id, client_id))
    except Exception as exc:
        logger.error(f"Celery batch task failed: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=5)
