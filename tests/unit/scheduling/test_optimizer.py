"""Tests for the SchedulerOptimizer."""

from __future__ import annotations

import pytest

from energy_scheduler.scheduling.models import InterruptibilityMode, ScheduleRequest
from energy_scheduler.scheduling.optimizer import SchedulerOptimizer
from tests.conftest import make_dt, make_price_series, make_task


@pytest.fixture()
def optimizer() -> SchedulerOptimizer:
    return SchedulerOptimizer(prefer_solver="heuristic")


class TestOptimizerNonInterruptible:
    def test_finds_cheapest_window(self, optimizer: SchedulerOptimizer) -> None:
        """Optimizer should find the cheapest known window (hours 2-3)."""
        prices = [0.25, 0.20, 0.05, 0.05, 0.25, 0.30]
        series = make_price_series(prices, start_hour=0, grid_minutes=60)
        task = make_task(earliest_hour=0, latest_hour=6, duration_minutes=120)
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = optimizer.solve(request)
        assert len(result.items) == 1
        item = result.items[0]
        assert item.start_at == make_dt(2)
        assert item.end_at == make_dt(4)

    def test_single_slot_task(self, optimizer: SchedulerOptimizer) -> None:
        """A 60-minute task should occupy exactly one hourly slot."""
        prices = [0.30, 0.05, 0.30, 0.30]
        series = make_price_series(prices, start_hour=0, grid_minutes=60)
        task = make_task(earliest_hour=0, latest_hour=4, duration_minutes=60)
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = optimizer.solve(request)
        assert len(result.items) == 1
        assert len(result.items[0].slots_used) == 1
        assert result.items[0].start_at == make_dt(1)


class TestOptimizerInterruptible:
    def test_interruptible_picks_non_contiguous_cheapest(
        self, optimizer: SchedulerOptimizer
    ) -> None:
        """Interruptible task optimizer should pick best individual slots."""
        prices = [0.50, 0.05, 0.50, 0.05, 0.50, 0.50]
        series = make_price_series(prices, start_hour=0, grid_minutes=60)
        task = make_task(
            0, 6, duration_minutes=120, interruptibility=InterruptibilityMode.interruptible
        )
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = optimizer.solve(request)
        assert len(result.items) == 1
        item = result.items[0]
        assert make_dt(1) in item.slots_used
        assert make_dt(3) in item.slots_used


class TestOptimizerEdgeCases:
    def test_empty_tasks(self, optimizer: SchedulerOptimizer) -> None:
        request = ScheduleRequest(date_label="2024-01-15", tasks=[], scheduler_grid_minutes=60)
        result = optimizer.solve(request)
        assert result.items == []
        assert result.unschedulable_task_ids == []

    def test_unschedulable_task_reported(self, optimizer: SchedulerOptimizer) -> None:
        series = make_price_series([0.10, 0.10], start_hour=0, grid_minutes=60)
        task = make_task(earliest_hour=0, latest_hour=1, duration_minutes=120)
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = optimizer.solve(request)
        assert task.id in result.unschedulable_task_ids
