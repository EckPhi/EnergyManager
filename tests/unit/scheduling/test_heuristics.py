"""Tests for the greedy heuristic planner."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from energy_scheduler.scheduling.heuristics import GreedyHeuristicPlanner
from energy_scheduler.scheduling.models import InterruptibilityMode, ScheduleRequest, Task
from tests.conftest import make_dt, make_price_series, make_task


@pytest.fixture()
def planner() -> GreedyHeuristicPlanner:
    return GreedyHeuristicPlanner()


class TestNonInterruptibleTasks:
    def test_picks_cheapest_contiguous_window(self, planner: GreedyHeuristicPlanner) -> None:
        """Scheduler should select the cheapest 2-hour window (02:00-04:00)."""
        prices = [0.20, 0.18, 0.05, 0.05, 0.20, 0.25, 0.30, 0.30]
        series = make_price_series(prices, start_hour=0, grid_minutes=60)
        task = make_task(earliest_hour=0, latest_hour=8, duration_minutes=120)
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = planner.solve(request)
        assert len(result.items) == 1
        item = result.items[0]
        assert item.start_at == make_dt(2)
        assert item.end_at == make_dt(4)

    def test_impossible_window_returns_unschedulable(self, planner: GreedyHeuristicPlanner) -> None:
        """A 3-hour task in a 2-hour window should be unschedulable."""
        series = make_price_series([0.10, 0.10], start_hour=6, grid_minutes=60)
        task = make_task(earliest_hour=6, latest_hour=8, duration_minutes=180)
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = planner.solve(request)
        assert len(result.items) == 0
        assert task.id in result.unschedulable_task_ids

    def test_higher_priority_task_scheduled_first(self, planner: GreedyHeuristicPlanner) -> None:
        """Higher-priority task should be allocated the cheap slots."""
        prices = [0.30, 0.05, 0.30, 0.30]
        series = make_price_series(prices, start_hour=0, grid_minutes=60)
        low_priority = make_task(0, 4, duration_minutes=60, priority=3)
        high_priority = make_task(0, 4, duration_minutes=60, priority=9)
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[low_priority, high_priority],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = planner.solve(request)
        assert len(result.items) == 2
        high_item = next(i for i in result.items if i.task_id == high_priority.id)
        assert high_item.start_at == make_dt(1)

    def test_price_spike_avoidance(self, planner: GreedyHeuristicPlanner) -> None:
        """Planner should avoid the expensive spike hour."""
        prices = [0.10, 1.00, 0.10, 0.10]
        series = make_price_series(prices, start_hour=0, grid_minutes=60)
        task = make_task(earliest_hour=0, latest_hour=4, duration_minutes=60)
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = planner.solve(request)
        assert len(result.items) == 1
        assert result.items[0].start_at != make_dt(1), "Should not schedule during price spike"

    def test_no_price_series_still_schedules(self, planner: GreedyHeuristicPlanner) -> None:
        """Without price data, the planner should still schedule (zero cost)."""
        task = make_task(earliest_hour=0, latest_hour=4, duration_minutes=60)
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task],
            price_series=None,
            scheduler_grid_minutes=60,
        )
        result = planner.solve(request)
        assert len(result.items) == 1

    def test_competing_tasks_no_overlap(self, planner: GreedyHeuristicPlanner) -> None:
        """Two non-interruptible tasks must not share slots."""
        prices = [0.05, 0.05, 0.30, 0.30]
        series = make_price_series(prices, start_hour=0, grid_minutes=60)
        task1 = make_task(0, 4, duration_minutes=60, priority=5)
        task2 = make_task(0, 4, duration_minutes=60, priority=5)
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task1, task2],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = planner.solve(request)
        scheduled = result.items
        if len(scheduled) == 2:
            slots1 = set(scheduled[0].slots_used)
            slots2 = set(scheduled[1].slots_used)
            assert not slots1.intersection(slots2), "Tasks must not share slots"


class TestInterruptibleTasks:
    def test_interruptible_picks_cheapest_slots(self, planner: GreedyHeuristicPlanner) -> None:
        """Interruptible task should use the two cheapest hours, even non-contiguous."""
        prices = [0.30, 0.05, 0.30, 0.05, 0.30, 0.30]
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
        result = planner.solve(request)
        assert len(result.items) == 1
        item = result.items[0]
        assert item.was_interrupted
        slot_prices = [prices[int((s - make_dt(0)).total_seconds() // 3600)] for s in item.slots_used]
        assert all(p <= 0.10 for p in slot_prices)

    def test_interruptible_impossible_if_not_enough_slots(
        self, planner: GreedyHeuristicPlanner
    ) -> None:
        """Interruptible task requiring 3 hours in a 2-hour window is unschedulable."""
        series = make_price_series([0.10, 0.10], start_hour=0, grid_minutes=60)
        task = make_task(
            0, 2, duration_minutes=180, interruptibility=InterruptibilityMode.interruptible
        )
        request = ScheduleRequest(
            date_label="2024-01-15",
            tasks=[task],
            price_series=series,
            scheduler_grid_minutes=60,
        )
        result = planner.solve(request)
        assert task.id in result.unschedulable_task_ids
