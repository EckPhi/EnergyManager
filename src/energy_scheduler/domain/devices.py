"""Core device domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class DeviceType(str, Enum):
    """Supported device categories."""

    washing_machine = "washing_machine"
    dishwasher = "dishwasher"
    ev_charger = "ev_charger"
    heat_pump = "heat_pump"
    water_heater = "water_heater"
    other = "other"


class InterruptibilityMode(str, Enum):
    """Whether a device run can be paused mid-cycle."""

    non_interruptible = "non_interruptible"
    interruptible = "interruptible"


@dataclass
class Device:
    """A physical or virtual smart device that can be scheduled."""

    name: str
    device_type: DeviceType
    rated_power_w: float
    interruptibility: InterruptibilityMode = InterruptibilityMode.non_interruptible
    id: UUID = field(default_factory=uuid4)
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Connector:
    """A connector integration that can control devices."""

    connector_type: str  # e.g. "home_assistant"
    base_url: str
    id: UUID = field(default_factory=uuid4)
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceBinding:
    """Links a Device to a Connector with integration-specific addressing."""

    device_id: UUID
    connector_id: UUID
    external_entity_id: str
    id: UUID = field(default_factory=uuid4)
    binding_config: dict[str, Any] = field(default_factory=dict)


@dataclass
class UsageTask:
    """A request to run a device for a given duration within a time window."""

    device_id: UUID
    required_duration_minutes: int
    earliest_start: datetime
    latest_end: datetime
    id: UUID = field(default_factory=uuid4)
    priority: int = 5
    user_notes: str = ""
