import pytest
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationType
from backend.app.models.client_business import ClientBusiness, BusinessType
from backend.app.models.ledger import ChartOfAccount, AccountType, VoucherType, EntrySide
from backend.app.models.invoice import Invoice, InvoiceType, ITCEligibility, ApprovalStatus
from backend.app.services.ledger_service import LedgerService
from backend.app.services.reconciliation_service import ReconciliationService
from backend.app.services.extraction_service import ExtractionService

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
async def test_reversal_voucher_handling(session: AsyncSession):
    user = User(email="rev@test.com", hashed_password="pwd", full_name="Reversal Tester")
    session.add(user)
    await session.flush()
    org = Organization(name="Rev Org", slug="rev-org", org_type=OrganizationType.FREELANCER)
    session.add(org)
    await session.flush()
    client = ClientBusiness(organization_id=org.id, legal_name="Rev Client", pan="ABCDE1234F", state_code="27")
    session.add(client)
    await session.flush()

    acc_bank = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="1001", account_name="Bank", account_type=AccountType.ASSET)
    acc_sales = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="4001", account_name="Sales", account_type=AccountType.INCOME)
    session.add_all([acc_bank, acc_sales])
    await session.flush()

    # Original entry: DR Bank 5000, CR Sales 5000
    orig_lines = [
        {"account_id": acc_bank.id, "entry_side": "DR", "amount": Decimal("5000.00")},
        {"account_id": acc_sales.id, "entry_side": "CR", "amount": Decimal("5000.00")}
    ]
    await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "ORIG-1", VoucherType.RECEIPT, "Original Payment", date.today(), orig_lines
    )

    # Reversal entry: DR Sales 5000, CR Bank 5000
    rev_lines = [
        {"account_id": acc_sales.id, "entry_side": "DR", "amount": Decimal("5000.00")},
        {"account_id": acc_bank.id, "entry_side": "CR", "amount": Decimal("5000.00")}
    ]
    rev_entry = await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "REV-1", VoucherType.REVERSAL, "Reversal of ORIG-1", date.today(), rev_lines
    )
    assert rev_entry.is_posted is True

    # Net trial balance should be exactly 0
    tb = await LedgerService.get_trial_balance(session, org.id, client.id)
    for b in tb:
        assert b["net_balance"] == Decimal("0.00")
