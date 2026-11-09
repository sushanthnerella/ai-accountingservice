import pytest
import uuid
from decimal import Decimal
from datetime import date
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.db.base import Base
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationType
from backend.app.models.client_business import ClientBusiness, BusinessType
from backend.app.models.ledger import ChartOfAccount, AccountType, VoucherType, EntrySide
from backend.app.models.invoice import Invoice, InvoiceType, ITCEligibility, ApprovalStatus
from backend.app.models.bank import BankAccount, BankTransaction, AccountType as BankAccountType, TransactionType
from backend.app.services.ledger_service import LedgerService
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
async def test_telangana_sole_proprietorship_accounting_scenario(session: AsyncSession):
    # Setup fresh organization & client business in Telangana (State Code 36)
    user = User(email="proprietor@telangana-accounting.in", hashed_password="pwd", full_name="Suresh Reddy")
    session.add(user)
    await session.flush()

    org = Organization(name="Suresh Enterprises", slug="suresh-enterprises", org_type=OrganizationType.FREELANCER)
    session.add(org)
    await session.flush()

    client = ClientBusiness(
        organization_id=org.id,
        legal_name="Suresh Enterprises",
        trade_name="Suresh Tech Services",
        business_type=BusinessType.PROPRIETORSHIP,
        pan="ABCDE1234F",
        gstin="36ABCDE1234F1Z5",
        state_code="36",
        is_composition_scheme=False
    )
    session.add(client)
    await session.flush()

    # Chart of Accounts setup
    acc_bank = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="1001", account_name="Current Bank Account", account_type=AccountType.ASSET)
    acc_ar = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="1002", account_name="Accounts Receivable (Customer)", account_type=AccountType.ASSET)
    acc_ap = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="2001", account_name="Accounts Payable (Supplier)", account_type=AccountType.LIABILITY)
    acc_equity = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="3001", account_name="Owner Capital", account_type=AccountType.EQUITY)
    acc_in_cgst = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="1003", account_name="Input CGST", account_type=AccountType.ASSET)
    acc_in_sgst = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="1004", account_name="Input SGST", account_type=AccountType.ASSET)
    acc_out_cgst = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="2002", account_name="Output CGST", account_type=AccountType.LIABILITY)
    acc_out_sgst = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="2003", account_name="Output SGST", account_type=AccountType.LIABILITY)
    acc_revenue = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="4001", account_name="Service Revenue", account_type=AccountType.INCOME)
    acc_expense = ChartOfAccount(organization_id=org.id, client_business_id=client.id, account_code="5001", account_name="Service Expenses", account_type=AccountType.EXPENSE)

    session.add_all([
        acc_bank, acc_ar, acc_ap, acc_equity, acc_in_cgst, acc_in_sgst,
        acc_out_cgst, acc_out_sgst, acc_revenue, acc_expense
    ])
    await session.flush()

    # Transaction 1: Owner capital introduced ₹100,000
    # DR Bank ₹100,000 / CR Owner Capital ₹100,000
    t1_lines = [
        {"account_id": acc_bank.id, "entry_side": "DR", "amount": Decimal("100000.00")},
        {"account_id": acc_equity.id, "entry_side": "CR", "amount": Decimal("100000.00")}
    ]
    await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "JV-001", VoucherType.RECEIPT, "Owner Capital Introduced", date.today(), t1_lines
    )

    # Transaction 2: Purchase service on credit: ₹10,000 + ₹900 CGST + ₹900 SGST = ₹11,800
    # DR Service Expense ₹10,000, DR Input CGST ₹900, DR Input SGST ₹900 / CR Accounts Payable ₹11,800
    t2_lines = [
        {"account_id": acc_expense.id, "entry_side": "DR", "amount": Decimal("10000.00")},
        {"account_id": acc_in_cgst.id, "entry_side": "DR", "amount": Decimal("900.00")},
        {"account_id": acc_in_sgst.id, "entry_side": "DR", "amount": Decimal("900.00")},
        {"account_id": acc_ap.id, "entry_side": "CR", "amount": Decimal("11800.00")}
    ]
    await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "JV-002", VoucherType.PURCHASE_BILL, "Credit Purchase with Input GST", date.today(), t2_lines
    )
    # Register Purchase Invoice for GST module
    purchase_inv = Invoice(
        organization_id=org.id,
        client_business_id=client.id,
        invoice_type=InvoiceType.PURCHASE,
        invoice_number="PUR-001",
        invoice_date=date.today(),
        counterparty_name="Tech Vendor LLP",
        place_of_supply_state_code="36",
        taxable_amount=Decimal("10000.00"),
        cgst_amount=Decimal("900.00"),
        sgst_amount=Decimal("900.00"),
        igst_amount=Decimal("0.00"),
        total_amount=Decimal("11800.00"),
        balance_due_amount=Decimal("11800.00"),
        itc_eligibility=ITCEligibility.ELIGIBLE_INPUT_SERVICES,
        approval_status=ApprovalStatus.APPROVED
    )
    session.add(purchase_inv)

    # Transaction 3: Sell service on credit: ₹20,000 + ₹1,800 CGST + ₹1,800 SGST = ₹23,600
    # DR Accounts Receivable ₹23,600 / CR Service Revenue ₹20,000, CR Output CGST ₹1,800, CR Output SGST ₹1,800
    t3_lines = [
        {"account_id": acc_ar.id, "entry_side": "DR", "amount": Decimal("23600.00")},
        {"account_id": acc_revenue.id, "entry_side": "CR", "amount": Decimal("20000.00")},
        {"account_id": acc_out_cgst.id, "entry_side": "CR", "amount": Decimal("1800.00")},
        {"account_id": acc_out_sgst.id, "entry_side": "CR", "amount": Decimal("1800.00")}
    ]
    await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "JV-003", VoucherType.SALES_INVOICE, "Credit Sales with Output GST", date.today(), t3_lines
    )
    sales_inv = Invoice(
        organization_id=org.id,
        client_business_id=client.id,
        invoice_type=InvoiceType.SALES,
        invoice_number="SAL-001",
        invoice_date=date.today(),
        counterparty_name="Acme Client Pvt Ltd",
        place_of_supply_state_code="36",
        taxable_amount=Decimal("20000.00"),
        cgst_amount=Decimal("1800.00"),
        sgst_amount=Decimal("1800.00"),
        igst_amount=Decimal("0.00"),
        total_amount=Decimal("23600.00"),
        balance_due_amount=Decimal("23600.00"),
        itc_eligibility=ITCEligibility.NOT_APPLICABLE,
        approval_status=ApprovalStatus.APPROVED
    )
    session.add(sales_inv)

    # Transaction 4: Receive ₹10,000 partial customer payment
    # DR Bank ₹10,000 / CR Accounts Receivable ₹10,000
    t4_lines = [
        {"account_id": acc_bank.id, "entry_side": "DR", "amount": Decimal("10000.00")},
        {"account_id": acc_ar.id, "entry_side": "CR", "amount": Decimal("10000.00")}
    ]
    await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "JV-004", VoucherType.RECEIPT, "Customer Partial Payment", date.today(), t4_lines
    )
    sales_inv.balance_due_amount -= Decimal("10000.00")

    # Transaction 5: Pay ₹5,000 partial supplier payment
    # DR Accounts Payable ₹5,000 / CR Bank ₹5,000
    t5_lines = [
        {"account_id": acc_ap.id, "entry_side": "DR", "amount": Decimal("5000.00")},
        {"account_id": acc_bank.id, "entry_side": "CR", "amount": Decimal("5000.00")}
    ]
    await LedgerService.post_journal_entry(
        session, org.id, client.id, user.id, "JV-005", VoucherType.PAYMENT, "Supplier Partial Payment", date.today(), t5_lines
    )
    purchase_inv.balance_due_amount -= Decimal("5000.00")
    await session.commit()

    # ==========================
    # INDEPENDENT AUDIT ASSERTIONS
    # ==========================
    tb = await LedgerService.get_trial_balance(session, org.id, client.id)
    balances = {b["account_code"]: b for b in tb}

    # 1. Bank: 100,000 (capital) + 10,000 (cust payment) - 5,000 (supplier payment) = 105,000
    assert balances["1001"]["net_balance"] == Decimal("105000.00")

    # 2. Accounts Receivable: 23,600 (billed) - 10,000 (received) = 13,600
    assert balances["1002"]["net_balance"] == Decimal("13600.00")
    assert sales_inv.balance_due_amount == Decimal("13600.00")

    # 3. Accounts Payable: -11,800 (billed CR) + 5,000 (paid DR) = -6,800 (CR balance 6,800)
    assert balances["2001"]["net_balance"] == Decimal("-6800.00")
    assert purchase_inv.balance_due_amount == Decimal("6800.00")

    # 4. Input Taxes
    assert balances["1003"]["net_balance"] == Decimal("900.00")  # Input CGST
    assert balances["1004"]["net_balance"] == Decimal("900.00")  # Input SGST

    # 5. Output Taxes (CR balances)
    assert balances["2002"]["net_balance"] == Decimal("-1800.00")  # Output CGST
    assert balances["2003"]["net_balance"] == Decimal("-1800.00")  # Output SGST

    # 6. Revenue & Expenses
    assert balances["4001"]["net_balance"] == Decimal("-20000.00")  # Revenue (CR)
    assert balances["5001"]["net_balance"] == Decimal("10000.00")   # Expense (DR)

    revenue = abs(balances["4001"]["net_balance"])
    expense = balances["5001"]["net_balance"]
    net_profit = revenue - expense
    assert net_profit == Decimal("10000.00")

    # 7. Trial Balance Total Debit & Credit
    total_dr = sum(b["total_debit"] for b in tb)
    total_cr = sum(b["total_credit"] for b in tb)
    assert total_dr == Decimal("130400.00")
    assert total_cr == Decimal("130400.00")

    # 8. Balance Sheet
    # Assets = Bank (105,000) + AR (13,600) + Input CGST (900) + Input SGST (900) = 120,400
    total_assets = (
        balances["1001"]["net_balance"] +
        balances["1002"]["net_balance"] +
        balances["1003"]["net_balance"] +
        balances["1004"]["net_balance"]
    )
    assert total_assets == Decimal("120400.00")

    # Liabilities = AP (6,800) + Output CGST (1,800) + Output SGST (1,800) = 10,400
    total_liabilities = (
        abs(balances["2001"]["net_balance"]) +
        abs(balances["2002"]["net_balance"]) +
        abs(balances["2003"]["net_balance"])
    )
    assert total_liabilities == Decimal("10400.00")

    # Equity including Profit = Owner Capital (100,000) + Net Profit (10,000) = 110,000
    owner_capital = abs(balances["3001"]["net_balance"])
    equity_with_profit = owner_capital + net_profit
    assert equity_with_profit == Decimal("110000.00")
    assert total_assets == total_liabilities + equity_with_profit

    # 9. GST Summary (GSTR-3B)
    gst_summary = await GSTService.compute_gstr_3b_summary(session, org.id, client.id)
    outward_tax = gst_summary["table_3_1_outward_supplies"]["total_tax"]
    eligible_itc = gst_summary["table_4_eligible_itc"]["total_itc"]
    net_gst_payable = (
        gst_summary["net_gst_payable"]["cgst"] +
        gst_summary["net_gst_payable"]["sgst"] +
        gst_summary["net_gst_payable"]["igst"]
    )
    assert outward_tax == Decimal("3600.00")  # 1800 + 1800
    assert eligible_itc == Decimal("1800.00") # 900 + 900
    assert net_gst_payable == Decimal("1800.00") # 3600 - 1800
