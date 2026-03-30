"""
SQLAlchemy async engine, declarative Base, and session factory.

All models import Base from here to ensure they share the same metadata
instance and can be reflected / migrated with Alembic.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=300,
)

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_all_tables() -> None:
    """Create all tables defined in the metadata (dev/test use only)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
