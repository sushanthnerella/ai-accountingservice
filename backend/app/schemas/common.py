from typing import Generic, List, Optional, TypeVar, Any, Dict
from pydantic import BaseModel

T = TypeVar("T")

class ResponseEnvelope(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    request_id: Optional[str] = None

class ErrorEnvelope(BaseModel):
    success: bool = False
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
