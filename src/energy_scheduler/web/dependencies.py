"""Shared FastAPI request dependencies."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from energy_scheduler.config import Settings, get_settings
from energy_scheduler.persistence.db import get_session
from energy_scheduler.scheduling.service import SchedulingService


async def get_db(
    session: AsyncSession = Depends(get_session),
) -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session."""
    yield session


def get_scheduling_service() -> SchedulingService:
    """Return a SchedulingService instance."""
    return SchedulingService()
