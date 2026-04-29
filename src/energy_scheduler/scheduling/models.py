"""Scheduling DTOs used by the optimizer and service layer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4


class InterruptibilityMode(str, Enum):
    """Whether a device task can be paused mid-run."""

    non_interruptible = "non_interruptible"
    interruptible = "interruptible"


@dataclass
class Task:
    """A device run request for the scheduler."""

    device_id: UUID
    required_duration_minutes: int
    earliest_start: datetime
    latest_end: datetime
    interruptibility: InterruptibilityMode = InterruptibilityMode.non_interruptible
    priority: int = 5
    rated_power_w: float = 1000.0
    id: UUID = field(default_factory=uuid4)
    notes: str = ""


@dataclass
class Constraint:
    """An additional user-defined scheduling constraint."""

    task_id: UUID
    not_before: datetime | None = None
    not_after: datetime | None = None
    max_cost_eur: float | None = None


@dataclass
class ScheduleRequest:
    """All inputs required by the scheduler to produce a schedule."""

    date_label: str
    tasks: list[Task] = field(default_factory=list)
    price_series: object | None = None  # must be SchedulerPriceSeries at runtime
    constraints: list[Constraint] = field(default_factory=list)
    scheduler_grid_minutes: int = 15
    id: UUID = field(default_factory=uuid4)


@dataclass
class ScheduleItem:
    """A single scheduled run window for a task."""

    task_id: UUID
    device_id: UUID
    start_at: datetime
    end_at: datetime
    estimated_cost_eur: float | None = None
    slots_used: list[datetime] = field(default_factory=list)
    was_interrupted: bool = False


@dataclass
class ScheduleResult:
    """The output of the scheduler for one ScheduleRequest."""

    request_id: UUID
    items: list[ScheduleItem] = field(default_factory=list)
    unschedulable_task_ids: list[UUID] = field(default_factory=list)
    solver: str = "unknown"
    solver_notes: str = ""
    produced_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
