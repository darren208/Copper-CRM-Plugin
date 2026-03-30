from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    environment: str


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check() -> HealthResponse:
    """Liveness/readiness probe endpoint for Cloud Run and load balancers."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc).isoformat(),
        environment=settings.app_env,
    )
