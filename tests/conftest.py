"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from energy_scheduler.pricing.contracts import (
    ConversionPolicy,
    SchedulerPricePoint,
    SchedulerPriceSeries,
)
from energy_scheduler.scheduling.models import InterruptibilityMode, Task


def make_dt(hour: int, minute: int = 0) -> datetime:
    """Create a UTC datetime for today at the given hour/minute."""
    return datetime(2024, 1, 15, hour, minute, tzinfo=timezone.utc)


def make_price_series(
    prices: list[float],
    start_hour: int = 0,
    grid_minutes: int = 60,
    provider: str = "test",
    region: str = "AT",
) -> SchedulerPriceSeries:
    """Build a SchedulerPriceSeries from a list of hourly prices."""
    from datetime import timedelta

    delta = timedelta(minutes=grid_minutes)
    points = []
    for i, price in enumerate(prices):
        slot_start = make_dt(start_hour) + delta * i
        points.append(
            SchedulerPricePoint(
                interval_start=slot_start,
                interval_end=slot_start + delta,
                price_per_kwh=price,
                currency="EUR",
            )
        )
    return SchedulerPriceSeries(
        provider=provider,
        region=region,
        grid_minutes=grid_minutes,
        valid_from=points[0].interval_start if points else make_dt(0),
        valid_to=points[-1].interval_end if points else make_dt(0),
        currency="EUR",
        conversion_policy=ConversionPolicy.proportional_expand,
        points=points,
    )


def make_task(
    earliest_hour: int,
    latest_hour: int,
    duration_minutes: int = 60,
    interruptibility: InterruptibilityMode = InterruptibilityMode.non_interruptible,
    priority: int = 5,
    rated_power_w: float = 1000.0,
) -> Task:
    """Build a Task spanning the given hours."""
    device_id = uuid4()
    return Task(
        device_id=device_id,
        required_duration_minutes=duration_minutes,
        earliest_start=make_dt(earliest_hour),
        latest_end=make_dt(latest_hour),
        interruptibility=interruptibility,
        priority=priority,
        rated_power_w=rated_power_w,
    )


@pytest.fixture()
def simple_price_series() -> SchedulerPriceSeries:
    """24-hour hourly price series with a cheap window 02:00-06:00."""
    prices = [
        0.20, 0.18, 0.08, 0.07, 0.07, 0.08,  # 00-06: cheap at 02-05
        0.15, 0.22, 0.28, 0.30, 0.32, 0.31,  # 06-12: rising
        0.29, 0.27, 0.25, 0.22, 0.20, 0.24,  # 12-18: moderate
        0.28, 0.30, 0.25, 0.22, 0.21, 0.19,  # 18-24: evening
    ]
    return make_price_series(prices, start_hour=0, grid_minutes=60)
