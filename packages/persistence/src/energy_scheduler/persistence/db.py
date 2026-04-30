"""SQLAlchemy engine and session management."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""


_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_db(database_url: str) -> None:
    """Initialise the async engine and session factory."""
    global _engine, _session_factory
    _engine = create_async_engine(database_url, echo=False, future=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def get_engine() -> object:  # AsyncEngine, but imported lazily to avoid circular dep
    """Return the current async engine."""
    if _engine is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    return _engine


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session (dependency injection compatible)."""
    if _session_factory is None:
        raise RuntimeError("Database not initialised. Call init_db() first.")
    async with _session_factory() as session:
        yield session
