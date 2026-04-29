"""Forecasting domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4


@dataclass
class ConsumptionObservation:
    """A single recorded energy consumption observation for a device run."""

    device_id: UUID
    observed_at: datetime
    duration_minutes: int
    energy_kwh: float
    id: UUID = field(default_factory=uuid4)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass
class ConsumptionProfile:
    """Aggregated consumption profile derived from historical observations."""

    device_id: UUID
    mean_duration_minutes: float
    mean_energy_kwh: float
    sample_count: int
    computed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    stddev_duration_minutes: float = 0.0
    stddev_energy_kwh: float = 0.0
    percentiles: dict[str, float] = field(default_factory=dict)
