"""
BhuSynch AI — Database Engine
==============================
SQLAlchemy async engine with PostGIS spatial extensions.
Maps to: Distributed Spatial Storage & Compute Core (Section 1)
         PostgreSQL 16 + PostGIS 3.4 (Authoritative Parcels & DB)
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# ── Async Engine (PostgreSQL 16 + PostGIS 3.4) ──────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "server_settings": {
            "application_name": "bhusynch_ai",
            "jit": "off",  # Disable JIT for PostGIS spatial queries
        }
    },
)

# ── Session Factory ──────────────────────────────────────────────────
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Declarative Base ────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    Base class for all ORM models.
    All spatial columns use SRID 7755 (EPSG:7755) as per NAKSHA standards.
    """
    pass


# ── Dependency Injection ─────────────────────────────────────────────
async def get_db() -> AsyncGenerator[Optional[AsyncSession], None]:
    """
    FastAPI dependency that provides a database session.
    Gracefully yields None if database is offline, enabling fallback to local datasets.
    """
    try:
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    except Exception:
        yield None


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[Optional[AsyncSession], None]:
    """
    Context manager variant for use outside FastAPI request cycle.
    """
    try:
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    except Exception:
        yield None


# ── Startup / Shutdown Hooks ─────────────────────────────────────────
async def init_db() -> None:
    """
    Initialize database: create PostGIS extension and all tables.
    Called during FastAPI lifespan startup. Gracefully handles offline DB.
    """
    try:
        async with engine.begin() as conn:
            # Enable PostGIS and UUID extensions (Section 3 DDL)
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
            # Create all ORM-mapped tables
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        # Non-fatal in prototype mode
        pass


async def close_db() -> None:
    """Dispose engine connections during shutdown."""
    try:
        await engine.dispose()
    except Exception:
        pass
