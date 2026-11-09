from fastapi import APIRouter
from backend.app.api.v1 import (
    auth, organizations, clients, documents, audit,
    invoices, banking, reconciliation, ledger, gst, tally, zoho
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(clients.router)
api_router.include_router(documents.router)
api_router.include_router(audit.router)
api_router.include_router(invoices.router)
api_router.include_router(banking.router)
api_router.include_router(reconciliation.router)
api_router.include_router(ledger.router)
api_router.include_router(gst.router)
api_router.include_router(tally.router)
api_router.include_router(zoho.router)
