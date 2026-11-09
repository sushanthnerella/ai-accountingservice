import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.models.invoice import InvoiceType, ITCEligibility, ApprovalStatus

class InvoiceItemCreate(BaseModel):
    description: str
    hsn_sac_code: Optional[str] = None
    quantity: Decimal = Decimal("1.0000")
    unit_price: Decimal
    taxable_amount: Decimal
    tax_rate_percent: Decimal = Decimal("18.00")

class InvoiceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    description: str
    hsn_sac_code: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    taxable_amount: Decimal
    tax_rate_percent: Decimal

class InvoiceCreate(BaseModel):
    document_id: Optional[uuid.UUID] = None
    invoice_type: InvoiceType = InvoiceType.SALES
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    counterparty_name: str
    counterparty_gstin: Optional[str] = None
    counterparty_state_code: Optional[str] = None
    place_of_supply_state_code: str
    taxable_amount: Decimal
    cgst_amount: Decimal = Decimal("0.0000")
    sgst_amount: Decimal = Decimal("0.0000")
    igst_amount: Decimal = Decimal("0.0000")
    cess_amount: Decimal = Decimal("0.0000")
    round_off_amount: Decimal = Decimal("0.0000")
    total_amount: Decimal
    itc_eligibility: ITCEligibility = ITCEligibility.PENDING
    is_reverse_charge: bool = False
    is_export_lut: bool = False
    lut_number: Optional[str] = None
    items: List[InvoiceItemCreate] = []

class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    client_business_id: uuid.UUID
    document_id: Optional[uuid.UUID] = None
    invoice_type: InvoiceType
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    counterparty_name: str
    counterparty_gstin: Optional[str] = None
    place_of_supply_state_code: str
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    cess_amount: Decimal
    total_amount: Decimal
    balance_due_amount: Decimal
    itc_eligibility: ITCEligibility
    approval_status: ApprovalStatus
    created_at: datetime
    items: List[InvoiceItemResponse] = []
