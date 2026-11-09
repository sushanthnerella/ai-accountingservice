from fastapi import APIRouter
from backend.app.api.v1 import auth, organizations, clients, documents, audit

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(clients.router)
api_router.include_router(documents.router)
api_router.include_router(audit.router)
