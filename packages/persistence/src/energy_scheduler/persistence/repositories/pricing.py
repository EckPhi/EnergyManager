"""Pricing repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from energy_scheduler.persistence.models import PriceSeriesORM


class PriceSeriesRepository:
    """CRUD operations for cached price series."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest(self, provider: str, region: str) -> PriceSeriesORM | None:
        result = await self._session.execute(
            select(PriceSeriesORM)
            .where(
                PriceSeriesORM.provider == provider,
                PriceSeriesORM.region == region,
            )
            .order_by(PriceSeriesORM.fetched_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def save(self, series: PriceSeriesORM) -> PriceSeriesORM:
        self._session.add(series)
        await self._session.flush()
        return series
