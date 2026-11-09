import pytest
import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.db.base import Base
from backend.app.models.organization import Organization, OrganizationType
from backend.app.models.client_business import ClientBusiness, BusinessType
from backend.app.models.user import User
from backend.app.models.ledger import ChartOfAccount, AccountType, VoucherType
from backend.app.services.ledger_service import LedgerService
from backend.app.services.tally_service import TallyService
from backend.app.services.zoho_service import ZohoService

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
async def test_tally_and_zoho_integrations(session: AsyncSession):
    user = User(email="sync@test.com", hashed_password="pwd", full_name="Sync Admin")
    session.add(user)
    await session.flush()

    org = Organization(name="Sync Org", slug="sync-org", org_type=OrganizationType.CA_FIRM)
    session.add(org)
    await session.flush()

    client = ClientBusiness(organization_id=org.id, legal_name="Sync Client", pan="ABCDE1234F", state_code="27")
    session.add(client)
    await session.flush()

    bank_acc = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="1001", account_name="HDFC Bank", account_type=AccountType.ASSET)
    sales_acc = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="4001", account_name="Sales", account_type=AccountType.INCOME)
    session.add_all([bank_acc, sales_acc])
    await session.flush()

    # Post a voucher
    lines = [
        {"account_id": bank_acc.id, "entry_side": "DR", "amount": Decimal("50000.00")},
        {"account_id": sales_acc.id, "entry_side": "CR", "amount": Decimal("50000.00")}
    ]
    await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "VOUCH-SYNC-1", VoucherType.RECEIPT, "Client remittance", date.today(), lines
    )

    # 1. Test Tally XML generation
    xml_str = await TallyService.generate_tally_xml(session, org.id, client.id)
    assert "<ENVELOPE>" in xml_str
    assert "VOUCH-SYNC-1" in xml_str
    assert "HDFC Bank" in xml_str

    # 2. Test Zoho sync
    zoho_res = await ZohoService.sync_approved_invoices(session, org.id, client.id)
    assert zoho_res["success"] is True
