import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationType
from backend.app.models.client_business import ClientBusiness, BusinessType
from backend.app.models.ledger import ChartOfAccount, AccountType, VoucherType, EntrySide, JournalEntry
from backend.app.models.invoice import Invoice, InvoiceType, ITCEligibility, ApprovalStatus
from backend.app.models.bank import BankAccount, BankTransaction, AccountType as BankAccountType, TransactionType
from backend.app.models.reconciliation import ReconciliationMatch, MatchScenario, TDSSection
from backend.app.services.ledger_service import LedgerService
from backend.app.services.reconciliation_service import ReconciliationService
from backend.app.services.extraction_service import ExtractionService
from backend.app.services.gst_service import GSTService

@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with session_factory() as s:
        yield s
    await engine.dispose()

@pytest.mark.asyncio
async def test_negative_unbalanced_journal_rejection(session: AsyncSession):
    user = User(email="neg1@test.com", hashed_password="pwd", full_name="Tester")
    session.add(user)
    await session.flush()
    org = Organization(name="Edge Org", slug="edge-org", org_type=OrganizationType.FREELANCER)
    session.add(org)
    await session.flush()
    client = ClientBusiness(organization_id=org.id, legal_name="Edge Client", pan="ABCDE1234F", state_code="27")
    session.add(client)
    await session.flush()

    acc1 = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="101", account_name="Bank", account_type=AccountType.ASSET)
    acc2 = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="401", account_name="Sales", account_type=AccountType.INCOME)
    session.add_all([acc1, acc2])
    await session.flush()

    # Unbalanced: DR 1000 != CR 900
    bad_lines = [
        {"account_id": acc1.id, "entry_side": "DR", "amount": Decimal("1000.00")},
        {"account_id": acc2.id, "entry_side": "CR", "amount": Decimal("900.00")}
    ]
    with pytest.raises(ValueError, match="Accounting Invariant Violation"):
        await LedgerService.post_journal_entry(
            session, org.id, client.id, user.id, "JV-ERR-1", VoucherType.RECEIPT, "Unbalanced Entry", date.today(), bad_lines
        )

@pytest.mark.asyncio
async def test_extraction_arithmetic_drift_rejection():
    # Discrepancy beyond tolerance (1000 + 90 + 90 != 1200)
    is_valid = ExtractionService.validate_arithmetic_invariants(
        taxable_amount=Decimal("1000.00"),
        cgst_amount=Decimal("90.00"),
        sgst_amount=Decimal("90.00"),
        igst_amount=Decimal("0.00"),
        cess_amount=Decimal("0.00"),
        round_off_amount=Decimal("0.00"),
        total_amount=Decimal("1200.00")
    )
    assert is_valid is False

@pytest.mark.asyncio
async def test_multi_rate_gst_and_pos_intra_inter_state_split():
    # 1. Intra-state supply (Maharashtra 27 -> Maharashtra 27)
    # Line 1: 5% GST on ₹1,000 -> CGST ₹25, SGST ₹25
    # Line 2: 18% GST on ₹2,000 -> CGST ₹180, SGST ₹180
    # Line 3: 28% GST on ₹500 -> CGST ₹70, SGST ₹70
    items = [
        {"taxable_amount": Decimal("1000.00"), "gst_rate": Decimal("5.00")},
        {"taxable_amount": Decimal("2000.00"), "gst_rate": Decimal("18.00")},
        {"taxable_amount": Decimal("500.00"), "gst_rate": Decimal("28.00")},
    ]
    intra_res = GSTService.calculate_multi_slab_invoice_taxes(
        supplier_gstin="27AAACB1234F1Z1",
        client_gstin="27XYZAB9876C1Z2",
        line_items=items
    )
    assert intra_res["is_intrastate"] is True
    assert intra_res["taxable_amount"] == Decimal("3500.00")
    assert intra_res["cgst_amount"] == Decimal("275.00")  # 25 + 180 + 70
    assert intra_res["sgst_amount"] == Decimal("275.00")  # 25 + 180 + 70
    assert intra_res["igst_amount"] == Decimal("0.00")
    assert intra_res["total_amount"] == Decimal("4050.00")

    # 2. Inter-state supply (Karnataka 29 -> Telangana 36)
    inter_res = GSTService.calculate_multi_slab_invoice_taxes(
        supplier_gstin="29AAACB1234F1Z1",
        client_gstin="36XYZAB9876C1Z2",
        line_items=items
    )
    assert inter_res["is_intrastate"] is False
    assert inter_res["taxable_amount"] == Decimal("3500.00")
    assert inter_res["cgst_amount"] == Decimal("0.00")
    assert inter_res["sgst_amount"] == Decimal("0.00")
    assert inter_res["igst_amount"] == Decimal("550.00")  # 50 + 360 + 140
    assert inter_res["total_amount"] == Decimal("4050.00")

@pytest.mark.asyncio
async def test_reconciliation_10_percent_tds_deduction_3_legged_entry(session: AsyncSession):
    user = User(email="ca_tds@test.com", hashed_password="pwd", full_name="CA Tester")
    session.add(user)
    await session.flush()
    org = Organization(name="Audit CA Practice", slug="audit-ca-tds", org_type=OrganizationType.CA_FIRM)
    session.add(org)
    await session.flush()
    client = ClientBusiness(organization_id=org.id, legal_name="Tech Client Pvt Ltd", pan="ABCDE5555F", gstin="27ABCDE5555F1Z1", state_code="27")
    session.add(client)
    await session.flush()

    # Open Sales Invoice: Base Taxable ₹100,000 + 18% GST (₹9k CGST + ₹9k SGST) = Total ₹118,000
    sales_inv = Invoice(
        organization_id=org.id,
        client_business_id=client.id,
        invoice_type=InvoiceType.SALES,
        invoice_number="TECH-2026-001",
        invoice_date=date.today(),
        counterparty_name="Enterprise Client India",
        place_of_supply_state_code="27",
        taxable_amount=Decimal("100000.00"),
        cgst_amount=Decimal("9000.00"),
        sgst_amount=Decimal("9000.00"),
        igst_amount=Decimal("0.00"),
        total_amount=Decimal("118000.00"),
        balance_due_amount=Decimal("118000.00"),
        approval_status=ApprovalStatus.APPROVED
    )
    session.add(sales_inv)

    # Bank remittance received: Customer deducted 10% TDS on base taxable (₹10,000), remitted ₹108,000
    bank_acc = BankAccount(
        organization_id=org.id,
        client_business_id=client.id,
        account_name="HDFC Current Account",
        bank_name="HDFC Bank",
        account_number="50200012345678",
        ifsc_code="HDFC0001234",
        opening_balance=Decimal("50000.00"),
        opening_balance_date=date.today(),
        current_ledger_balance=Decimal("50000.00")
    )
    session.add(bank_acc)
    await session.flush()

    txn = BankTransaction(
        organization_id=org.id,
        client_business_id=client.id,
        bank_account_id=bank_acc.id,
        transaction_date=date.today(),
        narration="NEFT CLR ENT CLIENT TDS DED 194J",
        transaction_type=TransactionType.CREDIT,
        amount=Decimal("108000.00"),
        running_balance=Decimal("158000.00"),
        unreconciled_amount=Decimal("108000.00")
    )
    session.add(txn)
    await session.flush()

    # Run match proposal
    matches = await ReconciliationService.generate_match_candidates(session, org.id, client.id)
    assert len(matches) == 1
    match = matches[0]
    assert match.match_scenario == MatchScenario.TDS_ADJUSTED_SETTLEMENT
    assert match.tds_section == TDSSection.SEC_194J_PROF
    assert match.tds_deducted_amount == Decimal("10000.00")
    assert match.allocated_amount == Decimal("108000.00")

    # Approve match
    approved_match = await ReconciliationService.approve_match(
        db=session,
        match_id=match.id,
        user_id=user.id,
        approved=True
    )
    assert approved_match.journal_entry_id is not None
    assert sales_inv.balance_due_amount == Decimal("0.00")

    # Verify 3-legged journal entry lines in General Ledger
    tb = await LedgerService.get_trial_balance(session, org.id, client.id, include_zero_balances=True)
    tb_map = {row["account_code"]: row for row in tb}
    # 1. Dr Bank (108,000)
    assert tb_map["1001"]["total_debit"] == Decimal("108000.00")
    # 2. Dr TDS Receivable (10,000)
    assert tb_map["1006"]["total_debit"] == Decimal("10000.00")
    # 3. Cr Accounts Receivable (118,000)
    assert tb_map["1002"]["total_credit"] == Decimal("118000.00")
    # Total Debits == Total Credits == 118,000
    assert sum(r["total_debit"] for r in tb) == sum(r["total_credit"] for r in tb) == Decimal("118000.00")

@pytest.mark.asyncio
async def test_posted_journal_entry_immutability_and_reversal(session: AsyncSession):
    user = User(email="audit_imm@test.com", hashed_password="pwd", full_name="Auditor")
    session.add(user)
    await session.flush()
    org = Organization(name="Immutable Org", slug="imm-org", org_type=OrganizationType.FREELANCER)
    session.add(org)
    await session.flush()
    client = ClientBusiness(organization_id=org.id, legal_name="Imm Client", pan="ABCDE1111F", state_code="27")
    session.add(client)
    await session.flush()

    acc1 = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="1001", account_name="Bank", account_type=AccountType.ASSET)
    acc2 = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="4001", account_name="Revenue", account_type=AccountType.INCOME)
    session.add_all([acc1, acc2])
    await session.flush()

    orig_entry = await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "POSTED-001", VoucherType.RECEIPT, "Client Payment", date.today(),
        [
            {"account_id": acc1.id, "entry_side": "DR", "amount": Decimal("25000.00")},
            {"account_id": acc2.id, "entry_side": "CR", "amount": Decimal("25000.00")}
        ]
    )
    assert orig_entry.is_posted is True

    # Attempt direct modification on posted entry must raise statutory invariant exception
    with pytest.raises(ValueError, match="Statutory Accounting Invariant Violation"):
        await LedgerService.modify_posted_journal_entry(orig_entry)

    # Correct statutory way: Create an immutable reversal entry
    reversal = await LedgerService.create_reversal_entry(
        session, orig_entry.id, user.id, reason="Client bounced cheque, voucher canceled"
    )
    assert reversal.voucher_type == VoucherType.REVERSAL
    assert reversal.is_posted is True

    # Balances must cancel out to exactly 0.00
    tb = await LedgerService.get_trial_balance(session, org.id, client.id, include_zero_balances=True)
    for row in tb:
        assert row["net_balance"] == Decimal("0.00")

@pytest.mark.asyncio
async def test_tenant_isolation_between_two_ca_clients(session: AsyncSession):
    user = User(email="multi_client@capractice.in", hashed_password="pwd", full_name="CA Senior")
    session.add(user)
    await session.flush()
    org = Organization(name="Multi Client CA Firm", slug="multi-ca", org_type=OrganizationType.CA_FIRM)
    session.add(org)
    await session.flush()

    client_a = ClientBusiness(organization_id=org.id, legal_name="Client A Tech", pan="AAAAA1111A", state_code="27")
    client_b = ClientBusiness(organization_id=org.id, legal_name="Client B Retail", pan="BBBBB2222B", state_code="29")
    session.add_all([client_a, client_b])
    await session.flush()

    # Create Invoice for Client A
    inv_a = Invoice(
        organization_id=org.id,
        client_business_id=client_a.id,
        invoice_type=InvoiceType.SALES,
        invoice_number="INV-A-101",
        invoice_date=date.today(),
        counterparty_name="Party A",
        place_of_supply_state_code="27",
        taxable_amount=Decimal("10000.00"),
        cgst_amount=Decimal("900.00"),
        sgst_amount=Decimal("900.00"),
        igst_amount=Decimal("0.00"),
        total_amount=Decimal("11800.00"),
        balance_due_amount=Decimal("11800.00"),
        approval_status=ApprovalStatus.APPROVED
    )
    # Create Invoice for Client B
    inv_b = Invoice(
        organization_id=org.id,
        client_business_id=client_b.id,
        invoice_type=InvoiceType.SALES,
        invoice_number="INV-B-202",
        invoice_date=date.today(),
        counterparty_name="Party B",
        place_of_supply_state_code="29",
        taxable_amount=Decimal("50000.00"),
        cgst_amount=Decimal("0.00"),
        sgst_amount=Decimal("0.00"),
        igst_amount=Decimal("9000.00"),
        total_amount=Decimal("59000.00"),
        balance_due_amount=Decimal("59000.00"),
        approval_status=ApprovalStatus.APPROVED
    )
    session.add_all([inv_a, inv_b])
    await session.flush()

    # Query scoped strictly to Client A
    q_a = select(Invoice).where(
        Invoice.organization_id == org.id,
        Invoice.client_business_id == client_a.id
    )
    res_a = (await session.execute(q_a)).scalars().all()
    assert len(res_a) == 1
    assert res_a[0].invoice_number == "INV-A-101"

    # Query scoped strictly to Client B
    q_b = select(Invoice).where(
        Invoice.organization_id == org.id,
        Invoice.client_business_id == client_b.id
    )
    res_b = (await session.execute(q_b)).scalars().all()
    assert len(res_b) == 1
    assert res_b[0].invoice_number == "INV-B-202"

    # Client A's GST summary must have zero exposure to Client B's ₹59,000 transaction
    gst_a = await GSTService.compute_gstr_3b_summary(session, org.id, client_a.id)
    assert gst_a["table_3_1_outward_supplies"]["taxable_amount"] == Decimal("10000.00")
    assert gst_a["table_3_1_outward_supplies"]["igst"] == Decimal("0.00")

    gst_b = await GSTService.compute_gstr_3b_summary(session, org.id, client_b.id)
    assert gst_b["table_3_1_outward_supplies"]["taxable_amount"] == Decimal("50000.00")
    assert gst_b["table_3_1_outward_supplies"]["igst"] == Decimal("9000.00")
