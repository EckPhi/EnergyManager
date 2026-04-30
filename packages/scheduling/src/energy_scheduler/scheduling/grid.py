"""Scheduler grid configuration and discretization helpers."""

from __future__ import annotations

from datetime import datetime, timedelta


class SchedulerGrid:
    """Manages grid resolution and slot arithmetic for the scheduler."""

    def __init__(self, grid_minutes: int = 15) -> None:
        if grid_minutes < 1 or grid_minutes > 1440:
            raise ValueError(f"grid_minutes must be 1-1440, got {grid_minutes}")
        self.grid_minutes = grid_minutes
        self.slot_duration = timedelta(minutes=grid_minutes)

    def snap_down(self, dt: datetime) -> datetime:
        """Snap a datetime down to the nearest grid boundary."""
        epoch = datetime(dt.year, dt.month, dt.day, tzinfo=dt.tzinfo)
        offset_s = (dt - epoch).total_seconds()
        grid_s = self.slot_duration.total_seconds()
        snapped_s = (offset_s // grid_s) * grid_s
        return epoch + timedelta(seconds=snapped_s)

    def snap_up(self, dt: datetime) -> datetime:
        """Snap a datetime up to the nearest grid boundary."""
        snapped = self.snap_down(dt)
        if snapped < dt:
            snapped += self.slot_duration
        return snapped

    def slots_needed(self, duration_minutes: int) -> int:
        """Return how many grid slots are needed to cover a given duration."""
        return -(-duration_minutes // self.grid_minutes)  # ceiling division

    def slots_in_window(self, start: datetime, end: datetime) -> int:
        """Return the number of grid slots between start and end."""
        delta_s = (end - start).total_seconds()
        return int(delta_s // self.slot_duration.total_seconds())

    def generate_slots(self, window_start: datetime, window_end: datetime) -> list[datetime]:
        """Return list of grid-aligned slot start times within the window."""
        start = self.snap_up(window_start)
        slots: list[datetime] = []
        current = start
        while current < window_end:
            slots.append(current)
            current += self.slot_duration
        return slots

    def slot_index(self, dt: datetime, reference: datetime) -> int:
        """Return the integer slot index of dt relative to reference."""
        delta_s = (self.snap_down(dt) - self.snap_down(reference)).total_seconds()
        return int(delta_s // self.slot_duration.total_seconds())
