import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.ledger import ChartOfAccount, JournalEntry, JournalLine, EntrySide, VoucherType, AccountType
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService

TWO_PLACES = Decimal("0.01")

class LedgerService:
    @staticmethod
    def get_indian_fy_dates(d: Optional[date] = None) -> Tuple[date, date, str]:
        """
        Computes Indian Financial Year (April 1 to March 31):
        - If month >= 4: April 1, Year -> March 31, Year + 1 (e.g. 2026-2027)
        - If month < 4: April 1, Year - 1 -> March 31, Year (e.g. 2025-2026)
        """
        ref_date = d or date.today()
        year = ref_date.year
        if ref_date.month >= 4:
            start_date = date(year, 4, 1)
            end_date = date(year + 1, 3, 31)
            fy_label = f"{year}-{year + 1}"
        else:
            start_date = date(year - 1, 4, 1)
            end_date = date(year, 3, 31)
            fy_label = f"{year - 1}-{year}"
        return start_date, end_date, fy_label

    @staticmethod
    def verify_entry_balanced(lines: List[JournalLine]) -> bool:
        """
        Inviolable Invariant:
        Sum(Debits) == Sum(Credits) strictly and > 0.
        """
        dr_sum = sum((l.amount for l in lines if l.entry_side == EntrySide.DR), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        cr_sum = sum((l.amount for l in lines if l.entry_side == EntrySide.CR), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        return dr_sum == cr_sum and dr_sum > Decimal("0.00")

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
        _, _, fy_label = LedgerService.get_indian_fy_dates(posting_date)

        entry = JournalEntry(
            organization_id=organization_id,
            client_business_id=client_business_id,
            entry_number=entry_number,
            posting_date=posting_date,
            financial_year=fy_label,
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
                amount=Decimal(str(line["amount"])).quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
                description=line.get("description")
            )
            db.add(j_line)
            lines.append(j_line)

        await db.flush()

        # Enforce double-entry invariant
        if not LedgerService.verify_entry_balanced(lines):
            dr = sum((l.amount for l in lines if l.entry_side == EntrySide.DR), Decimal("0.00"))
            cr = sum((l.amount for l in lines if l.entry_side == EntrySide.CR), Decimal("0.00"))
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
            payload_after={"entry_number": entry_number, "is_posted": True, "financial_year": fy_label}
        )

        return entry

    @staticmethod
    async def modify_posted_journal_entry(entry: JournalEntry, *args, **kwargs) -> None:
        """
        Enforces double-entry immutability under Indian accounting standards.
        Once an entry is POSTED, direct update or deletion is strictly forbidden.
        """
        if entry.is_posted:
            raise ValueError(
                "Statutory Accounting Invariant Violation: Posted journal entries are strictly immutable. "
                "Direct UPDATE or DELETE operations are prohibited. Create an immutable Reversal Journal Entry instead."
            )

    @staticmethod
    async def create_reversal_entry(
        db: AsyncSession,
        original_entry_id: uuid.UUID,
        user_id: uuid.UUID,
        reason: str
    ) -> JournalEntry:
        """
        Creates an immutable Reversal Journal Entry that mirrors and negates the original posted entry.
        """
        query = (
            select(JournalEntry)
            .where(JournalEntry.id == original_entry_id)
            .options(selectinload(JournalEntry.lines))
        )
        orig = (await db.execute(query)).scalar_one_or_none()
        if not orig:
            raise ValueError(f"Original journal entry {original_entry_id} not found")
        if not orig.is_posted:
            raise ValueError("Only posted journal entries can be reversed")

        rev_lines_data = []
        for line in orig.lines:
            rev_side = "CR" if line.entry_side == EntrySide.DR else "DR"
            rev_lines_data.append({
                "account_id": line.account_id,
                "entry_side": rev_side,
                "amount": line.amount,
                "description": f"Reversal of {orig.entry_number}: {reason}"
            })

        rev_entry_num = f"REV-{orig.entry_number}-{uuid.uuid4().hex[:4]}"
        reversal = await LedgerService.post_journal_entry(
            db=db,
            organization_id=orig.organization_id,
            client_business_id=orig.client_business_id,
            user_id=user_id,
            entry_number=rev_entry_num,
            voucher_type=VoucherType.REVERSAL,
            narration=f"Statutory Reversal of Voucher {orig.entry_number}. Reason: {reason}",
            posting_date=date.today(),
            lines_data=rev_lines_data
        )

        await AuditService.log_event(
            db=db,
            organization_id=orig.organization_id,
            user_id=user_id,
            event_type=AuditEventType.VOUCHER_POSTED,
            entity_name="JournalEntry",
            entity_id=str(reversal.id),
            payload_after={"reversal_of_entry_id": str(orig.id), "reversal_entry_number": rev_entry_num, "reason": reason}
        )
        return reversal

    @staticmethod
    async def get_trial_balance(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_zero_balances: bool = False
    ) -> List[Dict[str, Any]]:
        # Default to current Indian Financial Year (April 1 to March 31)
        fy_start, fy_end, _ = LedgerService.get_indian_fy_dates()
        s_date = start_date or fy_start
        e_date = end_date or fy_end

        query = (
            select(ChartOfAccount)
            .where(
                ChartOfAccount.organization_id == organization_id,
                ChartOfAccount.client_business_id == client_business_id
            )
            .options(
                selectinload(ChartOfAccount.journal_lines).selectinload(JournalLine.journal_entry)
            )
        )
        res = await db.execute(query)
        accounts = res.scalars().all()

        trial_balance = []
        for acc in accounts:
            valid_lines = [
                l for l in acc.journal_lines
                if l.journal_entry and l.journal_entry.is_posted
                and s_date <= l.journal_entry.posting_date <= e_date
            ]
            dr = sum((l.amount for l in valid_lines if l.entry_side == EntrySide.DR), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
            cr = sum((l.amount for l in valid_lines if l.entry_side == EntrySide.CR), Decimal("0.00")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

            if not include_zero_balances and dr == Decimal("0.00") and cr == Decimal("0.00"):
                continue

            trial_balance.append({
                "account_code": acc.account_code,
                "account_name": acc.account_name,
                "account_type": acc.account_type.value,
                "total_debit": dr,
                "total_credit": cr,
                "net_balance": dr - cr
            })
        return trial_balance

    @staticmethod
    async def get_profit_and_loss(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        tb = await LedgerService.get_trial_balance(
            db, organization_id, client_business_id, start_date, end_date, include_zero_balances=True
        )
        revenues = []
        expenses = []
        total_rev = Decimal("0.00")
        total_exp = Decimal("0.00")

        for row in tb:
            if row["account_type"] == AccountType.INCOME.value:
                rev_amt = abs(row["net_balance"])
                revenues.append({"code": row["account_code"], "name": row["account_name"], "amount": rev_amt})
                total_rev += rev_amt
            elif row["account_type"] == AccountType.EXPENSE.value:
                exp_amt = row["net_balance"]
                expenses.append({"code": row["account_code"], "name": row["account_name"], "amount": exp_amt})
                total_exp += exp_amt

        return {
            "revenues": revenues,
            "total_revenue": total_rev,
            "expenses": expenses,
            "total_expenses": total_exp,
            "net_profit": total_rev - total_exp
        }

    @staticmethod
    async def get_balance_sheet(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID,
        as_of_date: Optional[date] = None
    ) -> Dict[str, Any]:
        tb = await LedgerService.get_trial_balance(
            db, organization_id, client_business_id, end_date=as_of_date, include_zero_balances=True
        )
        pnl = await LedgerService.get_profit_and_loss(db, organization_id, client_business_id, end_date=as_of_date)

        assets = []
        liabilities = []
        equity = []

        total_assets = Decimal("0.00")
        total_liabilities = Decimal("0.00")
        total_equity = Decimal("0.00")

        for row in tb:
            if row["account_type"] == AccountType.ASSET.value:
                amt = row["net_balance"]
                assets.append({"code": row["account_code"], "name": row["account_name"], "amount": amt})
                total_assets += amt
            elif row["account_type"] == AccountType.LIABILITY.value:
                amt = abs(row["net_balance"])
                liabilities.append({"code": row["account_code"], "name": row["account_name"], "amount": amt})
                total_liabilities += amt
            elif row["account_type"] == AccountType.EQUITY.value:
                amt = abs(row["net_balance"])
                equity.append({"code": row["account_code"], "name": row["account_name"], "amount": amt})
                total_equity += amt

        equity_with_profit = total_equity + pnl["net_profit"]
        return {
            "assets": assets,
            "total_assets": total_assets,
            "liabilities": liabilities,
            "total_liabilities": total_liabilities,
            "equity": equity,
            "owner_capital": total_equity,
            "net_profit_period": pnl["net_profit"],
            "total_equity_with_profit": equity_with_profit,
            "is_balanced": (total_assets == total_liabilities + equity_with_profit)
        }
