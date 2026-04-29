#!/usr/bin/env python3
"""Demo setup script — seeds the database with example devices and tasks."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from energy_scheduler.config import get_settings
from energy_scheduler.persistence.db import init_db
from energy_scheduler.persistence.models import Base, DeviceORM, UsageTaskORM


async def seed() -> None:
    settings = get_settings()
    init_db(settings.database_url)

    from energy_scheduler.persistence.db import get_engine
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        device = DeviceORM(
            id=str(uuid4()),
            name="Washing Machine",
            device_type="washing_machine",
            rated_power_w=2000.0,
            interruptibility="non_interruptible",
        )
        session.add(device)

        now = datetime.now(timezone.utc)
        task = UsageTaskORM(
            id=str(uuid4()),
            device_id=device.id,
            required_duration_minutes=90,
            earliest_start=now,
            latest_end=now + timedelta(hours=8),
            priority=5,
        )
        session.add(task)
        await session.commit()
        print(f"Created device: {device.name} (id={device.id})")
        print(f"Created task: {task.id}")


if __name__ == "__main__":
    asyncio.run(seed())
