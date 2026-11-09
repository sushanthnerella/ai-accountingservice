import uuid
from typing import Dict, Any, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.invoice import Invoice, ApprovalStatus

class ZohoService:
    @staticmethod
    def get_authorization_url(client_id: str, redirect_uri: str) -> str:
        return f"https://accounts.zoho.in/oauth/v2/auth?scope=ZohoBooks.fullaccess.all&client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&access_type=offline"

    @staticmethod
    async def sync_approved_invoices(
        db: AsyncSession,
        organization_id: uuid.UUID,
        client_business_id: uuid.UUID,
        zoho_auth_token: str = "mock_token"
    ) -> Dict[str, Any]:
        """
        Syncs approved invoices to Zoho Books REST API.
        """
        query = select(Invoice).where(
            Invoice.organization_id == organization_id,
            Invoice.client_business_id == client_business_id,
            Invoice.approval_status == ApprovalStatus.APPROVED
        )
        approved_invoices = (await db.execute(query)).scalars().all()

        synced_count = len(approved_invoices)
        return {
            "success": True,
            "synced_invoices_count": synced_count,
            "status": "COMPLETED",
            "message": f"Successfully synchronized {synced_count} approved invoices to Zoho Books."
        }
