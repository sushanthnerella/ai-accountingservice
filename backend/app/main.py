import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.api.v1.router import api_router
from backend.app.schemas.common import ErrorEnvelope
import logging

setup_logging(settings.LOG_LEVEL)
logger = logging.getLogger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    yield
    logger.info("Application shutting down...")

app = FastAPI(title=settings.APP_NAME, description="Accounting Intelligence API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=ErrorEnvelope(error_code="VALIDATION_ERROR", message="Validation failed", details={"errors": exc.errors()}, request_id=str(uuid.uuid4())).model_dump())

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "environment": settings.APP_ENV}

@app.get("/ready", tags=["Health"])
async def readiness_check():
    return {"status": "ready"}
