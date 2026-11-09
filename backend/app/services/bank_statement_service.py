import uuid
from decimal import Decimal
from datetime import date
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.bank import BankAccount, BankTransaction, TransactionType, ClassificationCategory, ReconciliationStatus
from backend.app.models.document import Document

class BankStatementService:
    @staticmethod
    def assert_balance_invariant(
        opening_balance: Decimal,
        closing_balance: Decimal,
        transactions: List[Dict[str, Any]]
    ) -> bool:
        """
        Inviolable Invariant:
        Opening Balance + Sum(Credits) - Sum(Debits) == Closing Balance ± 0.01
        """
        total_credit = sum(Decimal(str(t["amount"])) for t in transactions if t["type"] == TransactionType.CREDIT)
        total_debit = sum(Decimal(str(t["amount"])) for t in transactions if t["type"] == TransactionType.DEBIT)
        expected_closing = opening_balance + total_credit - total_debit
        return abs(expected_closing - closing_balance) <= Decimal("0.0100")

    @staticmethod
    def classify_narration(narration: str, txn_type: TransactionType) -> ClassificationCategory:
        narration_upper = narration.upper()
        if "SALARY" in narration_upper or "PAYROLL" in narration_upper:
            return ClassificationCategory.OPERATING_EXPENSE
        elif "GST" in narration_upper or "CHALLAN" in narration_upper:
            return ClassificationCategory.TAX_PAYMENT_GST
        elif "ADVANCE TAX" in narration_upper or "INCOME TAX" in narration_upper:
            return ClassificationCategory.TAX_PAYMENT_ADVANCE_TAX
        elif "BANK CHARGES" in narration_upper or "SMS CHG" in narration_upper:
            return ClassificationCategory.BANK_CHARGES
        elif "INTEREST" in narration_upper:
            return ClassificationCategory.INTEREST_INCOME
        elif "DRAWING" in narration_upper or "PERSONAL" in narration_upper:
            return ClassificationCategory.OWNER_DRAWINGS
        elif "CONTRA" in narration_upper or "SELF TRANSFER" in narration_upper:
            return ClassificationCategory.INTERNAL_CONTRA
        elif txn_type == TransactionType.CREDIT:
            return ClassificationCategory.OPERATING_REVENUE
        else:
            return ClassificationCategory.OPERATING_EXPENSE

    @staticmethod
    async def parse_and_stage_transactions(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID,
        bank_account: BankAccount,
        raw_rows: List[Dict[str, Any]],
        document_id: Optional[uuid.UUID] = None
    ) -> List[BankTransaction]:
        running = bank_account.opening_balance
        staged_transactions: List[BankTransaction] = []

        for row in raw_rows:
            txn_type = TransactionType(row["type"])
            amt = Decimal(str(row["amount"]))
            if txn_type == TransactionType.CREDIT:
                running += amt
            else:
                running -= amt

            narration = row.get("narration", "Bank Transaction")
            category = BankStatementService.classify_narration(narration, txn_type)

            txn = BankTransaction(
                organization_id=organization_id,
                client_business_id=client_business_id,
                bank_account_id=bank_account.id,
                document_id=document_id,
                transaction_date=row.get("transaction_date", date.today()),
                value_date=row.get("value_date"),
                narration=narration,
                reference_number=row.get("reference_number"),
                utr_number=row.get("utr_number"),
                transaction_type=txn_type,
                amount=amt,
                running_balance=running,
                classification_category=category,
                reconciliation_status=ReconciliationStatus.UNRECONCILED,
                unreconciled_amount=amt
            )
            db.add(txn)
            staged_transactions.append(txn)

        bank_account.current_ledger_balance = running
        await db.flush()
        return staged_transactions
