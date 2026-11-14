import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone, date
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.reconciliation import ReconciliationMatch, MatchScenario, TDSSection, MatchApprovalStatus
from backend.app.models.bank import BankTransaction, ReconciliationStatus, TransactionType
from backend.app.models.invoice import Invoice, InvoiceType, ApprovalStatus
from backend.app.models.ledger import ChartOfAccount, AccountType, VoucherType, EntrySide
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService
from backend.app.services.ledger_service import LedgerService

TWO_PLACES = Decimal("0.01")

class ReconciliationService:
    @staticmethod
    def evaluate_tds_match(
        txn_amount: Decimal,
        invoice_total: Decimal,
        taxable_amount: Optional[Decimal] = None
    ) -> Tuple[bool, TDSSection, Decimal]:
        """
        Evaluates whether a transaction amount matches an invoice total subject to
        Indian TDS deductions on base taxable value under Sections 194J (10% Prof, 2% Tech)
        or 194C (1% Individual, 2% Company).
        In Indian Income Tax law, TDS is computed strictly on the base taxable value (excluding GST).
        """
        base_taxable = (taxable_amount if taxable_amount and taxable_amount > Decimal("0.00") else invoice_total)

        # 1. Section 194J Professional (10% TDS on taxable)
        tds_10 = (base_taxable * Decimal("0.10")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        expected_net_10 = invoice_total - tds_10
        if abs(txn_amount - expected_net_10) <= Decimal("1.00"):
            return True, TDSSection.SEC_194J_PROF, tds_10

        # Also support 10% on total (if client billed gross)
        tds_10_gross = (invoice_total * Decimal("0.10")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        if abs(txn_amount - (invoice_total - tds_10_gross)) <= Decimal("1.00"):
            return True, TDSSection.SEC_194J_PROF, tds_10_gross

        # 2. Section 194J Technical / 194C Company (2% TDS on taxable)
        tds_2 = (base_taxable * Decimal("0.02")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        expected_net_2 = invoice_total - tds_2
        if abs(txn_amount - expected_net_2) <= Decimal("1.00"):
            return True, TDSSection.SEC_194J_TECH, tds_2

        # 3. Section 194C Contractor - Individual/HUF (1% TDS on taxable)
        tds_1 = (base_taxable * Decimal("0.01")).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        expected_net_1 = invoice_total - tds_1
        if abs(txn_amount - expected_net_1) <= Decimal("1.00"):
            return True, TDSSection.SEC_194C, tds_1

        return False, TDSSection.NONE, Decimal("0.0000")

    @staticmethod
    async def generate_match_candidates(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID
    ) -> List[ReconciliationMatch]:
        # Fetch unreconciled transactions
        txns_q = select(BankTransaction).where(
            BankTransaction.organization_id == organization_id,
            BankTransaction.client_business_id == client_business_id,
            BankTransaction.reconciliation_status == ReconciliationStatus.UNRECONCILED
        )
        txns = (await db.execute(txns_q)).scalars().all()

        # Fetch open invoices
        invs_q = select(Invoice).where(
            Invoice.organization_id == organization_id,
            Invoice.client_business_id == client_business_id,
            Invoice.balance_due_amount > Decimal("0.0000")
        )
        invoices = (await db.execute(invs_q)).scalars().all()

        matches: List[ReconciliationMatch] = []

        for txn in txns:
            for inv in invoices:
                # 1. Exact 1-to-1 match
                if abs(txn.amount - inv.balance_due_amount) <= Decimal("0.01"):
                    match = ReconciliationMatch(
                        organization_id=organization_id,
                        client_business_id=client_business_id,
                        bank_transaction_id=txn.id,
                        invoice_id=inv.id,
                        match_scenario=MatchScenario.EXACT_ONE_TO_ONE,
                        allocated_amount=txn.amount,
                        tds_deducted_amount=Decimal("0.0000"),
                        tds_section=TDSSection.NONE,
                        confidence_score=Decimal("0.9800"),
                        match_rationale=f"Exact 1:1 match: Amount ₹{txn.amount} equals Invoice #{inv.invoice_number}",
                        approval_status=MatchApprovalStatus.PENDING
                    )
                    db.add(match)
                    matches.append(match)
                    break

                # 2. TDS Adjusted Settlement (10%, 2%, or 1%)
                is_tds, section, tds_amt = ReconciliationService.evaluate_tds_match(
                    txn.amount, inv.balance_due_amount, inv.taxable_amount
                )
                if is_tds:
                    match = ReconciliationMatch(
                        organization_id=organization_id,
                        client_business_id=client_business_id,
                        bank_transaction_id=txn.id,
                        invoice_id=inv.id,
                        match_scenario=MatchScenario.TDS_ADJUSTED_SETTLEMENT,
                        allocated_amount=txn.amount,
                        tds_deducted_amount=tds_amt,
                        tds_section=section,
                        confidence_score=Decimal("0.9500"),
                        match_rationale=(
                            f"High-Confidence Match with TDS Deduction under Sec {section.value}: "
                            f"Bank Remittance ₹{txn.amount} + TDS ₹{tds_amt} clears Invoice #{inv.invoice_number} (Total ₹{inv.balance_due_amount})"
                        ),
                        approval_status=MatchApprovalStatus.PENDING
                    )
                    db.add(match)
                    matches.append(match)
                    break

        await db.flush()
        return matches

    @staticmethod
    async def _get_or_create_account(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID,
        code: str,
        name: str,
        account_type: AccountType
    ) -> ChartOfAccount:
        q = select(ChartOfAccount).where(
            ChartOfAccount.client_business_id == client_business_id,
            ChartOfAccount.account_code == code
        )
        acc = (await db.execute(q)).scalar_one_or_none()
        if not acc:
            acc = ChartOfAccount(
                organization_id=organization_id,
                client_business_id=client_business_id,
                account_code=code,
                account_name=name,
                account_type=account_type
            )
            db.add(acc)
            await db.flush()
        return acc

    @staticmethod
    async def approve_match(
        db: AsyncSession,
        match_id: uuid.UUID,
        user_id: uuid.UUID,
        approved: bool = True,
        rejection_reason: Optional[str] = None
    ) -> ReconciliationMatch:
        match = await db.get(ReconciliationMatch, match_id)
        if not match:
            raise ValueError("Reconciliation match not found")

        if approved:
            match.approval_status = MatchApprovalStatus.APPROVED
            match.approved_by_user_id = user_id
            match.approved_at = datetime.now(timezone.utc)

            # Update bank txn and invoice statuses
            txn = await db.get(BankTransaction, match.bank_transaction_id)
            inv = await db.get(Invoice, match.invoice_id) if match.invoice_id else None

            if txn:
                txn.reconciliation_status = ReconciliationStatus.FULLY_RECONCILED
                txn.unreconciled_amount = Decimal("0.0000")

            if inv:
                total_cleared = (match.allocated_amount + match.tds_deducted_amount).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
                inv.balance_due_amount = max(Decimal("0.0000"), inv.balance_due_amount - total_cleared)
                inv.approval_status = ApprovalStatus.APPROVED

                # Automatically post balanced journal entries to the General Ledger
                if match.match_scenario == MatchScenario.TDS_ADJUSTED_SETTLEMENT or match.tds_deducted_amount > Decimal("0.0000"):
                    # 3-legged journal entry:
                    # 1. Dr Bank Account (actual bank remittance received)
                    # 2. Dr TDS Receivable (exact TDS deducted)
                    # 3. Cr Accounts Receivable / Party Ledger (full invoice total cleared)
                    acc_bank = await ReconciliationService._get_or_create_account(
                        db, match.organization_id, match.client_business_id, "1001", "Current Bank Account", AccountType.ASSET
                    )
                    acc_tds = await ReconciliationService._get_or_create_account(
                        db, match.organization_id, match.client_business_id, "1006", "TDS Receivable (Sec 194)", AccountType.ASSET
                    )
                    acc_ar = await ReconciliationService._get_or_create_account(
                        db, match.organization_id, match.client_business_id, "1002", "Accounts Receivable", AccountType.ASSET
                    )

                    lines = [
                        {"account_id": acc_bank.id, "entry_side": "DR", "amount": match.allocated_amount, "description": f"Bank remittance #{inv.invoice_number}"},
                        {"account_id": acc_tds.id, "entry_side": "DR", "amount": match.tds_deducted_amount, "description": f"TDS deduction Sec {match.tds_section.value}"},
                        {"account_id": acc_ar.id, "entry_side": "CR", "amount": total_cleared, "description": f"Invoice #{inv.invoice_number} cleared"}
                    ]

                    entry = await LedgerService.post_journal_entry(
                        db=db,
                        organization_id=match.organization_id,
                        client_business_id=match.client_business_id,
                        user_id=user_id,
                        entry_number=f"REC-{inv.invoice_number}-{uuid.uuid4().hex[:4]}",
                        voucher_type=VoucherType.RECEIPT,
                        narration=f"3-Legged TDS Settlement: Remittance ₹{match.allocated_amount} + TDS ₹{match.tds_deducted_amount} for #{inv.invoice_number}",
                        posting_date=txn.transaction_date if txn else date.today(),
                        lines_data=lines
                    )
                    match.journal_entry_id = entry.id

                elif match.match_scenario == MatchScenario.EXACT_ONE_TO_ONE:
                    acc_bank = await ReconciliationService._get_or_create_account(
                        db, match.organization_id, match.client_business_id, "1001", "Current Bank Account", AccountType.ASSET
                    )
                    if inv.invoice_type == InvoiceType.SALES:
                        acc_ar = await ReconciliationService._get_or_create_account(
                            db, match.organization_id, match.client_business_id, "1002", "Accounts Receivable", AccountType.ASSET
                        )
                        lines = [
                            {"account_id": acc_bank.id, "entry_side": "DR", "amount": match.allocated_amount, "description": f"Customer Receipt #{inv.invoice_number}"},
                            {"account_id": acc_ar.id, "entry_side": "CR", "amount": match.allocated_amount, "description": f"Accounts Receivable cleared #{inv.invoice_number}"}
                        ]
                        v_type = VoucherType.RECEIPT
                    else:
                        acc_ap = await ReconciliationService._get_or_create_account(
                            db, match.organization_id, match.client_business_id, "2001", "Accounts Payable", AccountType.LIABILITY
                        )
                        lines = [
                            {"account_id": acc_ap.id, "entry_side": "DR", "amount": match.allocated_amount, "description": f"Accounts Payable cleared #{inv.invoice_number}"},
                            {"account_id": acc_bank.id, "entry_side": "CR", "amount": match.allocated_amount, "description": f"Supplier Payment #{inv.invoice_number}"}
                        ]
                        v_type = VoucherType.PAYMENT

                    entry = await LedgerService.post_journal_entry(
                        db=db,
                        organization_id=match.organization_id,
                        client_business_id=match.client_business_id,
                        user_id=user_id,
                        entry_number=f"REC-{inv.invoice_number}-{uuid.uuid4().hex[:4]}",
                        voucher_type=v_type,
                        narration=f"1:1 Reconciliation Settlement for #{inv.invoice_number}",
                        posting_date=txn.transaction_date if txn else date.today(),
                        lines_data=lines
                    )
                    match.journal_entry_id = entry.id
        else:
            match.approval_status = MatchApprovalStatus.REJECTED
            match.rejection_reason = rejection_reason

        await db.flush()

        await AuditService.log_event(
            db=db,
            organization_id=match.organization_id,
            user_id=user_id,
            event_type=AuditEventType.MATCH_ACCEPTED if approved else AuditEventType.DOC_PROCESSING_STARTED,
            entity_name="ReconciliationMatch",
            entity_id=str(match.id),
            payload_after={"status": match.approval_status.value, "rejection_reason": rejection_reason}
        )

        return match
