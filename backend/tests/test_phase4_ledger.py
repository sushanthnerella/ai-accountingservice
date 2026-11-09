import pytest
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.db.base import Base
from backend.app.models.ledger import ChartOfAccount, AccountType, VoucherType, EntrySide
from backend.app.models.organization import Organization, OrganizationType
from backend.app.models.client_business import ClientBusiness, BusinessType
from backend.app.models.user import User
from backend.app.services.ledger_service import LedgerService

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
async def test_double_entry_balance_enforcement(session: AsyncSession):
    # Setup user, org, client, coa
    user = User(email="ca@ledger.com", hashed_password="pwd", full_name="Auditor")
    session.add(user)
    await session.flush()

    org = Organization(name="Ledger Org", slug="ledger-org", org_type=OrganizationType.CA_FIRM)
    session.add(org)
    await session.flush()

    client = ClientBusiness(
        organization_id=org.id,
        legal_name="Client Test",
        pan="ABCDE1234F",
        state_code="27",
        business_type=BusinessType.PVT_LTD
    )
    session.add(client)
    await session.flush()

    bank_acc = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="1001", account_name="HDFC Bank", account_type=AccountType.ASSET)
    sales_acc = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="4001", account_name="Consulting Sales", account_type=AccountType.INCOME)
    session.add_all([bank_acc, sales_acc])
    await session.flush()

    # 1. Balanced entry (Bank DR ₹1,18,000 / Sales CR ₹1,18,000)
    lines_balanced = [
        {"account_id": bank_acc.id, "entry_side": "DR", "amount": Decimal("118000.00")},
        {"account_id": sales_acc.id, "entry_side": "CR", "amount": Decimal("118000.00")}
    ]
    entry = await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "VOUCH-001", VoucherType.RECEIPT, "Client payment", date.today(), lines_balanced
    )
    assert entry.is_posted is True

    # 2. Unbalanced entry should raise ValueError
    lines_unbalanced = [
        {"account_id": bank_acc.id, "entry_side": "DR", "amount": Decimal("118000.00")},
        {"account_id": sales_acc.id, "entry_side": "CR", "amount": Decimal("100000.00")}
    ]
    with pytest.raises(ValueError, match="Accounting Invariant Violation"):
        await LedgerService.post_journal_entry(
            session, org.id, client.id, user.id, "VOUCH-002", VoucherType.RECEIPT, "Bad voucher", date.today(), lines_unbalanced
        )
