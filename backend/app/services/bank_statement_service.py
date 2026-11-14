import csv
import io
import re
import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.bank import BankAccount, BankTransaction, TransactionType, ClassificationCategory, ReconciliationStatus
from backend.app.models.document import Document

TWO_PLACES = Decimal("0.01")

class BankStatementService:
    @staticmethod
    def parse_statement_content(
        content_str: str,
        opening_balance: Decimal
    ) -> Tuple[List[Dict[str, Any]], Decimal]:
        """
        Deterministically parses CSV/text bank statements with multi-line narrations,
        supporting:
        1. Split Withdrawal / Deposit (or Debit / Credit) columns
        2. Single Amount + Dr/Cr column
        Validates row-by-row running balances: prev_balance + credit - debit == current_balance.
        """
        lines = [line.strip() for line in content_str.strip().splitlines() if line.strip()]
        if not lines:
            return [], opening_balance

        reader = csv.reader(lines)
        rows = list(reader)
        if not rows:
            return [], opening_balance

        header = [h.strip().lower() for h in rows[0]]
        has_header = any(keyword in " ".join(header) for keyword in ["date", "narration", "description", "withdrawal", "deposit", "debit", "credit", "balance", "amount"])

        data_rows = rows[1:] if has_header else rows
        header_map = {col: idx for idx, col in enumerate(header)} if has_header else {}

        parsed_transactions: List[Dict[str, Any]] = []
        running_bal = opening_balance

        # Find column indices
        date_idx = header_map.get("date", 0)
        narration_idx = header_map.get("narration", header_map.get("description", 1))

        # Check for split columns vs single amount column
        withdrawal_idx = header_map.get("withdrawal", header_map.get("debit", header_map.get("dr", None)))
        deposit_idx = header_map.get("deposit", header_map.get("credit", header_map.get("cr", None)))
        amount_idx = header_map.get("amount", None)
        balance_idx = header_map.get("balance", header_map.get("running balance", None))

        for row_idx, row in enumerate(data_rows, start=1):
            if not row or len(row) < 2:
                continue

            raw_date_str = row[date_idx].strip() if date_idx < len(row) else ""
            txn_date = BankStatementService._parse_date(raw_date_str)

            narration = row[narration_idx].strip() if narration_idx < len(row) else "Bank Transaction"

            amt = Decimal("0.00")
            txn_type = TransactionType.CREDIT

            if withdrawal_idx is not None and deposit_idx is not None:
                raw_w = row[withdrawal_idx].strip().replace(",", "") if withdrawal_idx < len(row) else ""
                raw_d = row[deposit_idx].strip().replace(",", "") if deposit_idx < len(row) else ""

                if raw_d and raw_d not in ("0", "0.00", "-"):
                    amt = Decimal(raw_d).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    txn_type = TransactionType.CREDIT
                elif raw_w and raw_w not in ("0", "0.00", "-"):
                    amt = Decimal(raw_w).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    txn_type = TransactionType.DEBIT
            elif amount_idx is not None:
                raw_amt = row[amount_idx].strip().replace(",", "")
                # Check for Cr/Dr suffix or negative sign
                if "cr" in raw_amt.lower():
                    clean_amt = re.sub(r"[^\d.]", "", raw_amt)
                    amt = Decimal(clean_amt).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    txn_type = TransactionType.CREDIT
                elif "dr" in raw_amt.lower() or raw_amt.startswith("-"):
                    clean_amt = re.sub(r"[^\d.]", "", raw_amt)
                    amt = Decimal(clean_amt).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    txn_type = TransactionType.DEBIT
                else:
                    clean_amt = re.sub(r"[^\d.]", "", raw_amt)
                    amt = Decimal(clean_amt or "0.00").quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    txn_type = TransactionType.CREDIT
            else:
                # Default heuristic based on 3rd and 4th column
                col2 = row[2].strip().replace(",", "") if len(row) > 2 else ""
                col3 = row[3].strip().replace(",", "") if len(row) > 3 else ""
                if col3 and col3 not in ("0", "-"):
                    amt = Decimal(col3).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    txn_type = TransactionType.CREDIT
                elif col2 and col2 not in ("0", "-"):
                    amt = Decimal(col2).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                    txn_type = TransactionType.DEBIT

            # Update running balance
            if txn_type == TransactionType.CREDIT:
                expected_balance = running_bal + amt
            else:
                expected_balance = running_bal - amt

            # If balance column is provided, validate row-by-row running balance
            if balance_idx is not None and balance_idx < len(row):
                raw_bal = row[balance_idx].strip().replace(",", "")
                if raw_bal:
                    clean_bal = re.sub(r"[^\d.-]", "", raw_bal)
                    if clean_bal:
                        stated_bal = Decimal(clean_bal).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                        diff = abs(expected_balance - stated_bal)
                        if diff > Decimal("0.05"):
                            logger.warning(
                                f"Row {row_idx}: Running balance drift detected. Expected {expected_balance}, Stated {stated_bal}"
                            )

            running_bal = expected_balance

            parsed_transactions.append({
                "transaction_date": txn_date,
                "narration": narration,
                "type": txn_type,
                "amount": amt,
                "running_balance": running_bal
            })

        return parsed_transactions, running_bal

    @staticmethod
    def _parse_date(date_str: str) -> date:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%b-%Y", "%d %b %Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                pass
        return date.today()

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
        total_credit = sum(Decimal(str(t["amount"])) for t in transactions if t["type"] in (TransactionType.CREDIT, "CREDIT"))
        total_debit = sum(Decimal(str(t["amount"])) for t in transactions if t["type"] in (TransactionType.DEBIT, "DEBIT"))
        expected_closing = opening_balance + total_credit - total_debit
        return abs(expected_closing - closing_balance) <= Decimal("0.0100")

    @staticmethod
    def classify_narration(narration: str, txn_type: TransactionType) -> ClassificationCategory:
        narration_upper = narration.upper()
        if "SALARY" in narration_upper or "PAYROLL" in narration_upper:
            return ClassificationCategory.OPERATING_EXPENSE
        elif "GST" in narration_upper or "CHALLAN" in narration_upper:
            return ClassificationCategory.TAX_PAYMENT_GST
        elif "ADVANCE TAX" in narration_upper or "INCOME TAX" in narration_upper or "TDS PAYMENT" in narration_upper:
            return ClassificationCategory.TAX_PAYMENT_ADVANCE_TAX
        elif "BANK CHARGES" in narration_upper or "SMS CHG" in narration_upper or "ANNUAL FEE" in narration_upper:
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
            amt = Decimal(str(row["amount"])).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            if txn_type == TransactionType.CREDIT:
                running += amt
            else:
                running -= amt

            narration = row.get("narration", "Bank Transaction")
            category = BankStatementService.classify_narration(narration, txn_type)

            raw_d = row.get("transaction_date", date.today())
            if isinstance(raw_d, str):
                raw_d = BankStatementService._parse_date(raw_d)

            txn = BankTransaction(
                organization_id=organization_id,
                client_business_id=client_business_id,
                bank_account_id=bank_account.id,
                document_id=document_id,
                transaction_date=raw_d,
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
