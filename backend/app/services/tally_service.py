import uuid
from decimal import Decimal
from typing import List
import xml.etree.ElementTree as ET
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.ledger import JournalEntry, JournalLine, EntrySide

class TallyService:
    @staticmethod
    async def generate_tally_xml(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID
    ) -> str:
        """
        Generates standard TDL-compliant XML envelope (<ENVELOPE><BODY><DATA><TALLYMESSAGE>...)
        for importing posted journal vouchers into TallyPrime.
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
        report_name.text = "All Masters and Vouchers"

        request_data = ET.SubElement(import_data, "REQUESTDATA")

        for entry in entries:
            tally_msg = ET.SubElement(request_data, "TALLYMESSAGE", {"xmlns:UDF": "TallyUDF"})
            voucher = ET.SubElement(tally_msg, "VOUCHER", {
                "VCHTYPE": entry.voucher_type.value,
                "ACTION": "Create",
                "OBJVIEW": "Accounting Voucher View"
            })

            # Date format YYYYMMDD
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
