import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from backend.app.models.client_business import BusinessType
import re

PAN_REGEX = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
GSTIN_REGEX = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"

class ClientBusinessCreateRequest(BaseModel):
    legal_name: str = Field(..., min_length=2, max_length=255)
    trade_name: Optional[str] = None
    business_type: BusinessType = BusinessType.PROPRIETORSHIP
    pan: str = Field(..., max_length=10)
    gstin: Optional[str] = Field(None, max_length=15)
    state_code: str = Field(..., min_length=2, max_length=2)
    is_composition_scheme: bool = False

    @field_validator("pan")
    @classmethod
    def validate_pan(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(PAN_REGEX, v):
            raise ValueError("Invalid Indian PAN format (must be 5 letters, 4 digits, 1 letter, e.g. ABCDE1234F)")
        return v

    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        v = v.strip().upper()
        if not re.match(GSTIN_REGEX, v):
            raise ValueError("Invalid Indian GSTIN format (e.g. 27ABCDE1234F1Z5)")
        return v

class ClientBusinessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    legal_name: str
    trade_name: Optional[str] = None
    business_type: BusinessType
    pan: str
    gstin: Optional[str] = None
    state_code: str
    is_composition_scheme: bool
    is_active: bool
    created_at: datetime
