"""Schedule repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from energy_scheduler.persistence.models import ScheduleItemORM, ScheduleORM


class ScheduleRepository:
    """CRUD operations for schedules and schedule items."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, schedule_id: str) -> ScheduleORM | None:
        result = await self._session.execute(
            select(ScheduleORM)
            .options(selectinload(ScheduleORM.items))
            .where(ScheduleORM.id == schedule_id)
        )
        return result.scalar_one_or_none()

    async def get_by_date(self, date_label: str) -> list[ScheduleORM]:
        result = await self._session.execute(
            select(ScheduleORM)
            .options(selectinload(ScheduleORM.items))
            .where(ScheduleORM.date_label == date_label)
        )
        return list(result.scalars().all())

    async def save(self, schedule: ScheduleORM) -> ScheduleORM:
        self._session.add(schedule)
        await self._session.flush()
        return schedule
