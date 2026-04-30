"""Baseline greedy/deterministic planner.

Implements the same interface as the optimizer. Scans all feasible windows sorted
by ascending cost and greedily assigns tasks in priority order.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from energy_scheduler.domain.pricing import SchedulerPriceSeries
from energy_scheduler.scheduling.grid import SchedulerGrid
from energy_scheduler.scheduling.models import (
    InterruptibilityMode,
    ScheduleItem,
    ScheduleRequest,
    ScheduleResult,
    Task,
)


class GreedyHeuristicPlanner:
    """Deterministic greedy planner that selects the cheapest feasible window."""

    def solve(self, request: ScheduleRequest) -> ScheduleResult:
        """Produce a schedule using a greedy cheapest-window heuristic.

        Args:
            request: The scheduling request including tasks and price series.

        Returns:
            ScheduleResult with assigned items and any unschedulable task IDs.
        """
        grid = SchedulerGrid(request.scheduler_grid_minutes)
        price_series: SchedulerPriceSeries | None = request.price_series  # type: ignore[assignment]

        # Build price lookup: slot_start → price_per_kwh
        price_map: dict[datetime, float] = {}
        if price_series is not None:
            for pt in price_series.points:
                price_map[pt.interval_start] = pt.price_per_kwh

        # Sort tasks by priority descending (higher priority first), then by duration
        tasks = sorted(request.tasks, key=lambda t: (-t.priority, t.required_duration_minutes))

        items: list[ScheduleItem] = []
        unschedulable: list[UUID] = []
        occupied_slots: set[datetime] = set()

        for task in tasks:
            result = self._schedule_task(task, grid, price_map, occupied_slots)
            if result is None:
                unschedulable.append(task.id)
            else:
                items.append(result)
                occupied_slots.update(result.slots_used)

        return ScheduleResult(
            request_id=request.id,
            items=items,
            unschedulable_task_ids=unschedulable,
            solver="greedy_heuristic",
        )

    def _schedule_task(
        self,
        task: Task,
        grid: SchedulerGrid,
        price_map: dict[datetime, float],
        occupied: set[datetime],
    ) -> ScheduleItem | None:
        """Find the cheapest feasible window for a single task."""
        slots_needed = grid.slots_needed(task.required_duration_minutes)
        available_slots = grid.generate_slots(task.earliest_start, task.latest_end)

        if task.interruptibility == InterruptibilityMode.non_interruptible:
            return self._find_cheapest_contiguous(
                task, available_slots, slots_needed, grid, price_map, occupied
            )
        else:
            return self._find_cheapest_interruptible(
                task, available_slots, slots_needed, grid, price_map, occupied
            )

    def _find_cheapest_contiguous(
        self,
        task: Task,
        available_slots: list[datetime],
        slots_needed: int,
        grid: SchedulerGrid,
        price_map: dict[datetime, float],
        occupied: set[datetime],
    ) -> ScheduleItem | None:
        """Find the cheapest contiguous block of slots for a non-interruptible task."""
        best_cost: float | None = None
        best_start_idx: int | None = None

        latest_end = task.latest_end
        slot_delta = grid.slot_duration

        for i in range(len(available_slots) - slots_needed + 1):
            window = available_slots[i : i + slots_needed]
            # Check window fits before latest_end
            if window[-1] + slot_delta > latest_end:
                break
            # Check no slot is occupied
            if any(s in occupied for s in window):
                continue
            cost = self._window_cost(window, price_map, task.rated_power_w, grid.grid_minutes)
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best_start_idx = i

        if best_start_idx is None:
            return None

        window = available_slots[best_start_idx : best_start_idx + slots_needed]
        start_at = window[0]
        end_at = window[-1] + slot_delta
        return ScheduleItem(
            task_id=task.id,
            device_id=task.device_id,
            start_at=start_at,
            end_at=end_at,
            estimated_cost_eur=best_cost,
            slots_used=list(window),
        )

    def _find_cheapest_interruptible(
        self,
        task: Task,
        available_slots: list[datetime],
        slots_needed: int,
        grid: SchedulerGrid,
        price_map: dict[datetime, float],
        occupied: set[datetime],
    ) -> ScheduleItem | None:
        """Pick the cheapest individual slots for an interruptible task."""
        free_slots = [s for s in available_slots if s not in occupied]
        slot_delta = grid.slot_duration

        if len(free_slots) < slots_needed:
            return None

        # Filter to slots within the task window
        valid_slots = [s for s in free_slots if s + slot_delta <= task.latest_end]
        if len(valid_slots) < slots_needed:
            return None

        sorted_slots = sorted(valid_slots, key=lambda s: price_map.get(s, 0.0))
        chosen = sorted(sorted_slots[:slots_needed])

        start_at = chosen[0]
        end_at = chosen[-1] + slot_delta
        cost = self._window_cost(chosen, price_map, task.rated_power_w, grid.grid_minutes)

        return ScheduleItem(
            task_id=task.id,
            device_id=task.device_id,
            start_at=start_at,
            end_at=end_at,
            estimated_cost_eur=cost,
            slots_used=chosen,
            was_interrupted=not _is_contiguous(chosen, slot_delta),
        )

    @staticmethod
    def _window_cost(
        slots: list[datetime],
        price_map: dict[datetime, float],
        rated_power_w: float,
        grid_minutes: int,
    ) -> float:
        """Estimate energy cost for a list of time slots."""
        energy_kwh_per_slot = (rated_power_w / 1000.0) * (grid_minutes / 60.0)
        total = 0.0
        for slot in slots:
            price = price_map.get(slot, 0.0)
            total += price * energy_kwh_per_slot
        return round(total, 6)


def _is_contiguous(slots: list[datetime], delta: timedelta) -> bool:
    return all(slots[i + 1] - slots[i] == delta for i in range(len(slots) - 1))
