import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict
from backend.app.models.bank import AccountType, TransactionType, ClassificationCategory, ReconciliationStatus

class BankAccountCreate(BaseModel):
    account_name: str
    account_number: str
    ifsc_code: str
    bank_name: str
    account_type: AccountType = AccountType.CURRENT
    opening_balance: Decimal = Decimal("0.0000")
    opening_balance_date: date

class BankAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    client_business_id: uuid.UUID
    account_name: str
    account_number: str
    ifsc_code: str
    bank_name: str
    account_type: AccountType
    opening_balance: Decimal
    current_ledger_balance: Decimal

class BankTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    client_business_id: uuid.UUID
    bank_account_id: uuid.UUID
    transaction_date: date
    value_date: Optional[date] = None
    narration: str
    reference_number: Optional[str] = None
    utr_number: Optional[str] = None
    transaction_type: TransactionType
    amount: Decimal
    running_balance: Decimal
    classification_category: ClassificationCategory
    reconciliation_status: ReconciliationStatus
    unreconciled_amount: Decimal
