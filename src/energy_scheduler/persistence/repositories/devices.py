"""Device and binding repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from energy_scheduler.persistence.models import ConnectorORM, DeviceBindingORM, DeviceORM


class DeviceRepository:
    """CRUD operations for Device and DeviceBinding records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_all(self) -> list[DeviceORM]:
        result = await self._session.execute(select(DeviceORM))
        return list(result.scalars().all())

    async def get_by_id(self, device_id: str) -> DeviceORM | None:
        return await self._session.get(DeviceORM, device_id)

    async def create(self, device: DeviceORM) -> DeviceORM:
        self._session.add(device)
        await self._session.flush()
        return device

    async def delete(self, device_id: str) -> bool:
        device = await self.get_by_id(device_id)
        if device is None:
            return False
        await self._session.delete(device)
        return True

    async def get_bindings(self, device_id: str) -> list[DeviceBindingORM]:
        result = await self._session.execute(
            select(DeviceBindingORM).where(DeviceBindingORM.device_id == device_id)
        )
        return list(result.scalars().all())
