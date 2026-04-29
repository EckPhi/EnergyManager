"""Scheduling domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4


class ScheduleStatus(str, Enum):
    """Lifecycle state of a schedule item."""

    pending = "pending"
    dispatched = "dispatched"
    running = "running"
    completed = "completed"
    skipped = "skipped"
    failed = "failed"


@dataclass
class UserConstraint:
    """An operator-defined constraint on when a device may run."""

    device_id: UUID
    not_before: datetime | None = None
    not_after: datetime | None = None
    prefer_before: datetime | None = None
    prefer_after: datetime | None = None
    max_cost_eur: float | None = None
    notes: str = ""


@dataclass
class ScheduleRequest:
    """All inputs required to produce a daily schedule."""

    date_label: str  # e.g. "2024-01-15"
    tasks: list[object] = field(default_factory=list)
    price_series: object | None = None  # SchedulerPriceSeries injected at call site
    constraints: list[UserConstraint] = field(default_factory=list)
    scheduler_grid_minutes: int = 15
    id: UUID = field(default_factory=uuid4)


@dataclass
class ScheduleItem:
    """A single scheduled run of a device."""

    task_id: UUID
    device_id: UUID
    start_at: datetime
    end_at: datetime
    estimated_cost_eur: float | None = None
    status: ScheduleStatus = ScheduleStatus.pending
    id: UUID = field(default_factory=uuid4)


@dataclass
class ScheduleResult:
    """The output of the scheduling optimiser for one request."""

    request_id: UUID
    items: list[ScheduleItem] = field(default_factory=list)
    unschedulable_task_ids: list[UUID] = field(default_factory=list)
    solver_notes: str = ""
    produced_at: datetime = field(default_factory=datetime.utcnow)
