import uuid
from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.reconciliation import MatchScenario, TDSSection, MatchApprovalStatus

class MatchApprovalRequest(BaseModel):
    approval_status: MatchApprovalStatus
    rejection_reason: Optional[str] = None

class ReconciliationMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    client_business_id: uuid.UUID
    bank_transaction_id: uuid.UUID
    invoice_id: Optional[uuid.UUID] = None
    match_scenario: MatchScenario
    allocated_amount: Decimal
    tds_deducted_amount: Decimal
    tds_section: TDSSection
    confidence_score: Decimal
    match_rationale: str
    approval_status: MatchApprovalStatus
    created_at: datetime
