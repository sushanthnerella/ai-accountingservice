import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict
from backend.app.models.document import DocumentStatus, DocumentCategory

class UploadedFileInfo(BaseModel):
    document_id: uuid.UUID
    file_name: str
    sha256_hash: str
    status: DocumentStatus
    is_duplicate: bool
    duplicate_of_id: Optional[uuid.UUID] = None

class BatchUploadResponse(BaseModel):
    batch_id: uuid.UUID
    batch_reference: str
    total_files: int
    uploaded_files: List[UploadedFileInfo]

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    client_business_id: uuid.UUID
    batch_id: Optional[uuid.UUID] = None
    original_filename: str
    file_size_bytes: int
    mime_type: str
    sha256_hash: str
    category: DocumentCategory
    status: DocumentStatus
    is_duplicate: bool
    duplicate_of_id: Optional[uuid.UUID] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
