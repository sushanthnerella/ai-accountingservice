import uuid
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

async def set_tenant_context(session: AsyncSession, org_id: Optional[uuid.UUID] = None, client_id: Optional[uuid.UUID] = None) -> None:
    """
    Executes transaction-scoped PostgreSQL configuration to enforce Row-Level Security (RLS)
    without connection-pool leakage across requests.
    Passing is_local=true guarantees configuration terminates automatically when transaction ends.
    """
    bind = session.bind
    dialect_name = bind.dialect.name if bind else "postgresql"
    if dialect_name == "postgresql":
        org_val = str(org_id) if org_id else ""
        client_val = str(client_id) if client_id else ""
        await session.execute(
            text(
                "SELECT set_config('app.current_org_id', :org_val, true), "
                "set_config('app.current_organization_id', :org_val, true), "
                "set_config('app.current_client_id', :client_val, true)"
            ),
            {"org_val": org_val, "client_val": client_val}
        )

async def reset_tenant_context(session: AsyncSession) -> None:
    bind = session.bind
    dialect_name = bind.dialect.name if bind else "postgresql"
    if dialect_name == "postgresql":
        await session.execute(
            text(
                "SELECT set_config('app.current_org_id', '', true), "
                "set_config('app.current_organization_id', '', true), "
                "set_config('app.current_client_id', '', true)"
            )
        )
