import uuid
from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.ledger import AccountType, VoucherType, EntrySide

class COACreate(BaseModel):
    account_code: str
    account_name: str
    account_type: AccountType

class COAResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    account_code: str
    account_name: str
    account_type: AccountType

class JournalLineCreate(BaseModel):
    account_id: uuid.UUID
    line_number: int
    entry_side: EntrySide
    amount: Decimal
    description: Optional[str] = None

class JournalLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    account_id: uuid.UUID
    line_number: int
    entry_side: EntrySide
    amount: Decimal
    description: Optional[str] = None

class JournalEntryCreate(BaseModel):
    entry_number: str
    posting_date: date
    financial_year: str = "2024-2025"
    voucher_type: VoucherType
    narration: str
    lines: List[JournalLineCreate]

class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    entry_number: str
    posting_date: date
    financial_year: str
    voucher_type: VoucherType
    narration: str
    is_posted: bool
    created_at: datetime
    lines: List[JournalLineResponse] = []
