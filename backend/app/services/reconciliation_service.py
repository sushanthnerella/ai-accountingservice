import uuid
from decimal import Decimal
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.reconciliation import ReconciliationMatch, MatchScenario, TDSSection, MatchApprovalStatus
from backend.app.models.bank import BankTransaction, ReconciliationStatus, TransactionType
from backend.app.models.invoice import Invoice, ApprovalStatus
from backend.app.models.audit import AuditEventType
from backend.app.services.audit_service import AuditService

class ReconciliationService:
    @staticmethod
    def evaluate_tds_match(txn_amount: Decimal, invoice_total: Decimal) -> Tuple[bool, TDSSection, Decimal]:
        """
        Evaluates whether a transaction amount matches an invoice total subject to
        Indian Section 194J Professional (10%), Tech (2%), or 194C (1% or 2%) TDS deductions.
        """
        # Check 10% TDS (Invoice - 10% = Txn)
        expected_90 = invoice_total * Decimal("0.90")
        if abs(txn_amount - expected_90) <= Decimal("1.00"):
            tds_deducted = invoice_total * Decimal("0.10")
            return True, TDSSection.SEC_194J_PROF, tds_deducted

        # Check 2% TDS (Invoice - 2% = Txn)
        expected_98 = invoice_total * Decimal("0.98")
        if abs(txn_amount - expected_98) <= Decimal("1.00"):
            tds_deducted = invoice_total * Decimal("0.02")
            return True, TDSSection.SEC_194J_TECH, tds_deducted

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

                # 2. TDS Adjusted Settlement (10% or 2%)
                is_tds, section, tds_amt = ReconciliationService.evaluate_tds_match(txn.amount, inv.balance_due_amount)
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
                        match_rationale=f"TDS adjusted settlement under Sec {section.value}: Net received ₹{txn.amount} + TDS ₹{tds_amt} clears Invoice #{inv.invoice_number}",
                        approval_status=MatchApprovalStatus.PENDING
                    )
                    db.add(match)
                    matches.append(match)
                    break

        await db.flush()
        return matches

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
            if txn:
                txn.reconciliation_status = ReconciliationStatus.FULLY_RECONCILED
                txn.unreconciled_amount = Decimal("0.0000")

            if match.invoice_id:
                inv = await db.get(Invoice, match.invoice_id)
                if inv:
                    inv.balance_due_amount = max(Decimal("0.0000"), inv.balance_due_amount - (match.allocated_amount + match.tds_deducted_amount))
                    inv.approval_status = ApprovalStatus.APPROVED
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
