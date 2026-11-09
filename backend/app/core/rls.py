import uuid
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

async def set_tenant_context(session: AsyncSession, org_id: Optional[uuid.UUID] = None, client_id: Optional[uuid.UUID] = None) -> None:
    bind = session.bind
    dialect_name = bind.dialect.name if bind else "postgresql"
    if dialect_name == "postgresql":
        org_val = str(org_id) if org_id else ""
        client_val = str(client_id) if client_id else ""
        await session.execute(text(f"SET LOCAL app.current_org_id = '{org_val}'"))
        await session.execute(text(f"SET LOCAL app.current_client_id = '{client_val}'"))

async def reset_tenant_context(session: AsyncSession) -> None:
    bind = session.bind
    dialect_name = bind.dialect.name if bind else "postgresql"
    if dialect_name == "postgresql":
        await session.execute(text("RESET ALL"))
