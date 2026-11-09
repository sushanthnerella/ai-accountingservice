import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db.session import get_db
from backend.app.schemas.document import BatchUploadResponse, DocumentResponse, UploadedFileInfo
from backend.app.schemas.common import ResponseEnvelope
from backend.app.services.document_service import DocumentService
from backend.app.models.document import Document, DocumentCategory
from backend.app.api.deps import get_current_user, get_tenant_context
from backend.app.models.user import User
from backend.app.tasks.document_tasks import process_document_batch_task

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/upload", response_model=ResponseEnvelope[BatchUploadResponse], status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    files: List[UploadFile] = File(...),
    category: DocumentCategory = Form(DocumentCategory.AUTO_DETECT),
    pdf_password: Optional[str] = Form(None),
    user: User = Depends(get_current_user),
    tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context),
    db: AsyncSession = Depends(get_db)
):
    org_id, client_id = tenant_ctx
    if not org_id or not client_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "Organization and Client Business headers are required"})

    file_tuples = []
    for file in files:
        content = await file.read()
        file_tuples.append((file.filename, content))

    try:
        batch = await DocumentService.process_upload_batch(db=db, organization_id=org_id, client_business_id=client_id, user_id=user.id, files=file_tuples, category=category)
        await db.commit()
        await db.refresh(batch, ["documents"])

        try:
            process_document_batch_task.delay(str(batch.id), str(org_id), str(client_id))
        except Exception:
            pass

        uploaded_files = [
            UploadedFileInfo(document_id=doc.id, file_name=doc.original_filename, sha256_hash=doc.sha256_hash, status=doc.status, is_duplicate=doc.is_duplicate, duplicate_of_id=doc.duplicate_of_id)
            for doc in batch.documents
        ]

        return ResponseEnvelope(data=BatchUploadResponse(batch_id=batch.id, batch_reference=batch.batch_reference, total_files=batch.total_files, uploaded_files=uploaded_files), message="Batch accepted for processing")
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "UPLOAD_FAILED", "message": str(e)})

@router.get("", response_model=ResponseEnvelope[List[DocumentResponse]])
async def list_documents(tenant_ctx: tuple[Optional[uuid.UUID], Optional[uuid.UUID]] = Depends(get_tenant_context), db: AsyncSession = Depends(get_db)):
    org_id, client_id = tenant_ctx
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error_code": "HEADER_MISSING", "message": "X-Organization-Id header is required"})
    query = select(Document).where(Document.organization_id == org_id)
    if client_id:
        query = query.where(Document.client_business_id == client_id)
    query = query.order_by(Document.created_at.desc())
    res = await db.execute(query)
    return ResponseEnvelope(data=[DocumentResponse.model_validate(d) for d in res.scalars().all()])
