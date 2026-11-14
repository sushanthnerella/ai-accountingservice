import uuid
from decimal import Decimal
from typing import List, Optional
import xml.etree.ElementTree as ET
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.ledger import JournalEntry, JournalLine, EntrySide, ChartOfAccount, AccountType, VoucherType

class TallyService:
    @staticmethod
    def _map_account_to_tally_group(account_name: str, account_type: AccountType) -> str:
        name_upper = account_name.upper()
        if "BANK" in name_upper:
            return "Bank Accounts"
        elif "RECEIVABLE" in name_upper or "DEBTOR" in name_upper or "CUSTOMER" in name_upper:
            return "Sundry Debtors"
        elif "PAYABLE" in name_upper or "CREDITOR" in name_upper or "SUPPLIER" in name_upper:
            return "Sundry Creditors"
        elif "CGST" in name_upper or "SGST" in name_upper or "IGST" in name_upper or "TAX" in name_upper or "TDS" in name_upper:
            return "Duties & Taxes"
        elif account_type == AccountType.ASSET:
            return "Current Assets"
        elif account_type == AccountType.LIABILITY:
            return "Current Liabilities"
        elif account_type == AccountType.EQUITY:
            return "Capital Account"
        elif account_type == AccountType.INCOME:
            return "Sales Accounts"
        elif account_type == AccountType.EXPENSE:
            return "Indirect Expenses"
        return "Suspense A/c"

    @staticmethod
    def _map_voucher_type_to_tally(voucher_type: VoucherType) -> str:
        mapping = {
            VoucherType.SALES_INVOICE: "Sales",
            VoucherType.PURCHASE_BILL: "Purchase",
            VoucherType.RECEIPT: "Receipt",
            VoucherType.PAYMENT: "Payment",
            VoucherType.CONTRA: "Contra",
            VoucherType.JOURNAL_ADJUSTMENT: "Journal",
            VoucherType.REVERSAL: "Journal"
        }
        return mapping.get(voucher_type, "Journal")

    @staticmethod
    async def generate_tally_masters_xml(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID
    ) -> str:
        """
        Generates standard Tally Prime Masters.xml containing all ledger accounts
        organized into standard statutory Tally groups.
        """
        q = select(ChartOfAccount).where(
            ChartOfAccount.organization_id == organization_id,
            ChartOfAccount.client_business_id == client_business_id
        )
        accounts = (await db.execute(q)).scalars().all()

        envelope = ET.Element("ENVELOPE")
        header = ET.SubElement(envelope, "HEADER")
        tally_req = ET.SubElement(header, "TALLYREQUEST")
        tally_req.text = "Import Data"

        body = ET.SubElement(envelope, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        req_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(req_desc, "REPORTNAME")
        report_name.text = "All Masters"

        request_data = ET.SubElement(import_data, "REQUESTDATA")

        for acc in accounts:
            tally_msg = ET.SubElement(request_data, "TALLYMESSAGE", {"xmlns:UDF": "TallyUDF"})
            ledger = ET.SubElement(tally_msg, "LEDGER", {"NAME": acc.account_name, "ACTION": "Create"})

            name_el = ET.SubElement(ledger, "NAME")
            name_el.text = acc.account_name

            parent_el = ET.SubElement(ledger, "PARENT")
            parent_el.text = TallyService._map_account_to_tally_group(acc.account_name, acc.account_type)

            opening_bal = ET.SubElement(ledger, "OPENINGBALANCE")
            opening_bal.text = "0.00"

        return ET.tostring(envelope, encoding="utf-8", xml_declaration=True).decode("utf-8")

    @staticmethod
    async def generate_tally_vouchers_xml(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID
    ) -> str:
        """
        Generates standard TDL-compliant XML envelope for importing posted vouchers into Tally Prime.
        """
        query = (
            select(JournalEntry)
            .where(
                JournalEntry.organization_id == organization_id,
                JournalEntry.client_business_id == client_business_id,
                JournalEntry.is_posted == True
            )
            .options(selectinload(JournalEntry.lines).selectinload(JournalLine.account))
        )
        entries = (await db.execute(query)).scalars().all()

        envelope = ET.Element("ENVELOPE")
        header = ET.SubElement(envelope, "HEADER")
        tally_req = ET.SubElement(header, "TALLYREQUEST")
        tally_req.text = "Import Data"

        body = ET.SubElement(envelope, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        req_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(req_desc, "REPORTNAME")
        report_name.text = "Vouchers"

        request_data = ET.SubElement(import_data, "REQUESTDATA")

        for entry in entries:
            tally_msg = ET.SubElement(request_data, "TALLYMESSAGE", {"xmlns:UDF": "TallyUDF"})
            tally_vch_type = TallyService._map_voucher_type_to_tally(entry.voucher_type)
            voucher = ET.SubElement(tally_msg, "VOUCHER", {
                "VCHTYPE": tally_vch_type,
                "ACTION": "Create",
                "OBJVIEW": "Accounting Voucher View"
            })

            vch_date = ET.SubElement(voucher, "DATE")
            vch_date.text = entry.posting_date.strftime("%Y%m%d")

            vch_num = ET.SubElement(voucher, "VOUCHERNUMBER")
            vch_num.text = entry.entry_number

            narration = ET.SubElement(voucher, "NARRATION")
            narration.text = entry.narration

            guid = ET.SubElement(voucher, "GUID")
            guid.text = str(entry.id)

            for line in entry.lines:
                ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
                ledger_name = ET.SubElement(ledger_entry, "LEDGERNAME")
                ledger_name.text = line.account.account_name if line.account else "Suspense Account"

                is_debit = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
                is_debit.text = "Yes" if line.entry_side == EntrySide.DR else "No"

                amount = ET.SubElement(ledger_entry, "AMOUNT")
                # Tally convention: positive for Credit, negative for Debit
                val = -abs(line.amount) if line.entry_side == EntrySide.DR else abs(line.amount)
                amount.text = f"{val:.2f}"

        return ET.tostring(envelope, encoding="utf-8", xml_declaration=True).decode("utf-8")

    @staticmethod
    async def generate_tally_package_xml(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID
    ) -> str:
        """
        Generates single combined package containing both Masters and Vouchers.
        """
        # Fetch accounts
        q_acc = select(ChartOfAccount).where(
            ChartOfAccount.organization_id == organization_id,
            ChartOfAccount.client_business_id == client_business_id
        )
        accounts = (await db.execute(q_acc)).scalars().all()

        # Fetch vouchers
        q_entries = (
            select(JournalEntry)
            .where(
                JournalEntry.organization_id == organization_id,
                JournalEntry.client_business_id == client_business_id,
                JournalEntry.is_posted == True
            )
            .options(selectinload(JournalEntry.lines).selectinload(JournalLine.account))
        )
        entries = (await db.execute(q_entries)).scalars().all()

        envelope = ET.Element("ENVELOPE")
        header = ET.SubElement(envelope, "HEADER")
        tally_req = ET.SubElement(header, "TALLYREQUEST")
        tally_req.text = "Import Data"

        body = ET.SubElement(envelope, "BODY")
        import_data = ET.SubElement(body, "IMPORTDATA")
        req_desc = ET.SubElement(import_data, "REQUESTDESC")
        report_name = ET.SubElement(req_desc, "REPORTNAME")
        report_name.text = "All Masters and Vouchers"

        request_data = ET.SubElement(import_data, "REQUESTDATA")

        # 1. Add Masters
        for acc in accounts:
            tally_msg = ET.SubElement(request_data, "TALLYMESSAGE", {"xmlns:UDF": "TallyUDF"})
            ledger = ET.SubElement(tally_msg, "LEDGER", {"NAME": acc.account_name, "ACTION": "Create"})
            name_el = ET.SubElement(ledger, "NAME")
            name_el.text = acc.account_name
            parent_el = ET.SubElement(ledger, "PARENT")
            parent_el.text = TallyService._map_account_to_tally_group(acc.account_name, acc.account_type)
            opening_bal = ET.SubElement(ledger, "OPENINGBALANCE")
            opening_bal.text = "0.00"

        # 2. Add Vouchers
        for entry in entries:
            tally_msg = ET.SubElement(request_data, "TALLYMESSAGE", {"xmlns:UDF": "TallyUDF"})
            tally_vch_type = TallyService._map_voucher_type_to_tally(entry.voucher_type)
            voucher = ET.SubElement(tally_msg, "VOUCHER", {
                "VCHTYPE": tally_vch_type,
                "ACTION": "Create",
                "OBJVIEW": "Accounting Voucher View"
            })
            vch_date = ET.SubElement(voucher, "DATE")
            vch_date.text = entry.posting_date.strftime("%Y%m%d")
            vch_num = ET.SubElement(voucher, "VOUCHERNUMBER")
            vch_num.text = entry.entry_number
            narration = ET.SubElement(voucher, "NARRATION")
            narration.text = entry.narration
            guid = ET.SubElement(voucher, "GUID")
            guid.text = str(entry.id)

            for line in entry.lines:
                ledger_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
                ledger_name = ET.SubElement(ledger_entry, "LEDGERNAME")
                ledger_name.text = line.account.account_name if line.account else "Suspense Account"
                is_debit = ET.SubElement(ledger_entry, "ISDEEMEDPOSITIVE")
                is_debit.text = "Yes" if line.entry_side == EntrySide.DR else "No"
                amount = ET.SubElement(ledger_entry, "AMOUNT")
                val = -abs(line.amount) if line.entry_side == EntrySide.DR else abs(line.amount)
                amount.text = f"{val:.2f}"

        return ET.tostring(envelope, encoding="utf-8", xml_declaration=True).decode("utf-8")

    # Backward-compatible alias
    generate_tally_xml = generate_tally_package_xml
