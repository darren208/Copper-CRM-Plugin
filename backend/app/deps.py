from typing import AsyncGenerator, Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import AsyncSessionFactory
from app.services.copper import CopperService
from app.utils.security import decode_jwt_token
from app.config import settings
import structlog

logger = structlog.get_logger(__name__)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async SQLAlchemy session and ensure it is closed after use."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_copper_service(
    x_copper_token: Annotated[str | None, Header()] = None,
) -> CopperService:
    """
    Return a CopperService initialised with the Bearer token supplied by the
    Copper plugin iframe via the X-Copper-Token request header.
    """
    if not x_copper_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Copper-Token header is required",
        )
    return CopperService(access_token=x_copper_token)


async def verify_agent_token(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """
    Validate a JWT bearer token issued by this service.
    Returns the decoded payload (agent_id, role, exp …).
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must use Bearer scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_jwt_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return payload


# Convenience type aliases for use in route signatures
DBSession = Annotated[AsyncSession, Depends(get_db)]
AgentPayload = Annotated[dict, Depends(verify_agent_token)]
CopperSvc = Annotated[CopperService, Depends(get_copper_service)]
