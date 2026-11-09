from backend.app.tasks.celery_app import celery_app
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="tasks.process_document_batch", bind=True, max_retries=3)
def process_document_batch_task(self, batch_id: str, organization_id: str, client_id: str):
    logger.info(f"Processing batch {batch_id} for org {organization_id}, client {client_id}")
    return {"batch_id": batch_id, "status": "PROCESSING", "stage": "INGESTED_WAITING_OCR"}
