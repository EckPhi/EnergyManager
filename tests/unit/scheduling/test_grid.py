"""Tests for SchedulerGrid discretization."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from energy_scheduler.scheduling.grid import SchedulerGrid


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 15, hour, minute, tzinfo=timezone.utc)


class TestGrid15:
    def test_snap_down_aligned(self) -> None:
        grid = SchedulerGrid(15)
        assert grid.snap_down(dt(10, 0)) == dt(10, 0)

    def test_snap_down_mid_slot(self) -> None:
        grid = SchedulerGrid(15)
        assert grid.snap_down(dt(10, 7)) == dt(10, 0)

    def test_snap_up_aligned(self) -> None:
        grid = SchedulerGrid(15)
        assert grid.snap_up(dt(10, 0)) == dt(10, 0)

    def test_snap_up_mid_slot(self) -> None:
        grid = SchedulerGrid(15)
        assert grid.snap_up(dt(10, 3)) == dt(10, 15)

    def test_slots_needed_exact(self) -> None:
        grid = SchedulerGrid(15)
        assert grid.slots_needed(60) == 4

    def test_slots_needed_ceiling(self) -> None:
        grid = SchedulerGrid(15)
        assert grid.slots_needed(70) == 5

    def test_generate_slots_count(self) -> None:
        grid = SchedulerGrid(15)
        slots = grid.generate_slots(dt(0, 0), dt(2, 0))
        assert len(slots) == 8

    def test_slot_index(self) -> None:
        grid = SchedulerGrid(15)
        assert grid.slot_index(dt(1, 0), dt(0, 0)) == 4


class TestGrid30:
    def test_slots_needed(self) -> None:
        grid = SchedulerGrid(30)
        assert grid.slots_needed(90) == 3

    def test_generate_24h(self) -> None:
        grid = SchedulerGrid(30)
        slots = grid.generate_slots(dt(0), dt(0).replace(day=16))
        assert len(slots) == 48


class TestGrid60:
    def test_slots_in_window(self) -> None:
        grid = SchedulerGrid(60)
        end = datetime(2024, 1, 16, 0, tzinfo=timezone.utc)
        assert grid.slots_in_window(dt(0), end) == 24

    def test_invalid_grid_raises(self) -> None:
        with pytest.raises(ValueError):
            SchedulerGrid(0)
