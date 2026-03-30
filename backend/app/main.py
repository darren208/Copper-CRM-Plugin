from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import settings
from app.models.db import engine, Base
from app.utils.logging import setup_structlog
from app.api import health, webhooks, review, contacts, copper_oauth, plugin

setup_structlog()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "startup",
        env=settings.app_env,
        version=settings.app_version,
        base_url=settings.app_base_url,
    )
    # Verify database connectivity
    try:
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession
        async with AsyncSession(engine) as session:
            await session.execute(text("SELECT 1"))
        logger.info("database_connected")
    except Exception as exc:
        logger.error("database_connection_failed", error=str(exc))
        # Do not prevent startup; let health check surface the issue

    yield

    logger.info("shutdown")
    await engine.dispose()


app = FastAPI(
    title="Davidson Insurance – Copper CRM AI Plugin",
    version=settings.app_version,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router, tags=["health"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(review.router, prefix="/api/v1", tags=["review"])
app.include_router(contacts.router, prefix="/api/v1", tags=["contacts"])
app.include_router(copper_oauth.router, prefix="/oauth", tags=["oauth"])
app.include_router(plugin.router, prefix="/api/v1/plugin", tags=["plugin"])


# ── Global exception handlers ────────────────────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning("validation_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )
