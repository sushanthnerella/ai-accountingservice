import uuid
from decimal import Decimal
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.ledger import ChartOfAccount, JournalEntry, JournalLine, EntrySide, VoucherType, AccountType
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService

class LedgerService:
    @staticmethod
    def verify_entry_balanced(lines: List[JournalLine]) -> bool:
        """
        Inviolable Invariant:
        Sum(Debits) == Sum(Credits) strictly.
        """
        dr_sum = sum(l.amount for l in lines if l.entry_side == EntrySide.DR)
        cr_sum = sum(l.amount for l in lines if l.entry_side == EntrySide.CR)
        return dr_sum == cr_sum and dr_sum > Decimal("0.0000")

    @staticmethod
    async def post_journal_entry(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID,
        user_id: uuid.UUID,
        entry_number: str,
        voucher_type: VoucherType,
        narration: str,
        posting_date: date,
        lines_data: List[Dict[str, Any]]
    ) -> JournalEntry:
        entry = JournalEntry(
            organization_id=organization_id,
            client_business_id=client_business_id,
            entry_number=entry_number,
            posting_date=posting_date,
            voucher_type=voucher_type,
            narration=narration,
            is_posted=False
        )
        db.add(entry)
        await db.flush()

        lines: List[JournalLine] = []
        for idx, line in enumerate(lines_data, start=1):
            j_line = JournalLine(
                journal_entry_id=entry.id,
                account_id=line["account_id"],
                line_number=idx,
                entry_side=EntrySide(line["entry_side"]),
                amount=Decimal(str(line["amount"])),
                description=line.get("description")
            )
            db.add(j_line)
            lines.append(j_line)

        await db.flush()

        # Enforce double-entry invariant
        if not LedgerService.verify_entry_balanced(lines):
            dr = sum(l.amount for l in lines if l.entry_side == EntrySide.DR)
            cr = sum(l.amount for l in lines if l.entry_side == EntrySide.CR)
            raise ValueError(f"Accounting Invariant Violation: Total Debits ({dr}) != Total Credits ({cr})")

        entry.is_posted = True
        entry.posted_at = datetime.now(timezone.utc)
        await db.flush()

        await AuditService.log_event(
            db=db,
            organization_id=organization_id,
            user_id=user_id,
            event_type=AuditEventType.VOUCHER_POSTED,
            entity_name="JournalEntry",
            entity_id=str(entry.id),
            payload_after={"entry_number": entry_number, "is_posted": True}
        )

        return entry

    @staticmethod
    async def get_trial_balance(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        # Calculate debit and credit totals per account
        query = (
            select(ChartOfAccount)
            .where(
                ChartOfAccount.organization_id == organization_id,
                ChartOfAccount.client_business_id == client_business_id
            )
            .options(selectinload(ChartOfAccount.journal_lines))
        )
        res = await db.execute(query)
        accounts = res.scalars().all()

        trial_balance = []
        for acc in accounts:
            dr = sum(l.amount for l in acc.journal_lines if l.entry_side == EntrySide.DR)
            cr = sum(l.amount for l in acc.journal_lines if l.entry_side == EntrySide.CR)
            trial_balance.append({
                "account_code": acc.account_code,
                "account_name": acc.account_name,
                "account_type": acc.account_type.value,
                "total_debit": dr,
                "total_credit": cr,
                "net_balance": dr - cr
            })
        return trial_balance
