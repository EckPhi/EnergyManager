"""Scheduling application service coordinating inputs and outputs."""

from __future__ import annotations

from energy_scheduler.scheduling.models import ScheduleRequest, ScheduleResult
from energy_scheduler.scheduling.optimizer import SchedulerOptimizer


class SchedulingService:
    """Coordinates schedule request validation and optimizer invocation."""

    def __init__(self, optimizer: SchedulerOptimizer | None = None) -> None:
        self._optimizer = optimizer or SchedulerOptimizer()

    def schedule(self, request: ScheduleRequest) -> ScheduleResult:
        """Validate and execute a scheduling request.

        Args:
            request: The scheduling request.

        Returns:
            ScheduleResult from the optimizer.

        Raises:
            ValueError: If the request is malformed.
        """
        self._validate(request)
        return self._optimizer.solve(request)

    def _validate(self, request: ScheduleRequest) -> None:
        if request.scheduler_grid_minutes < 1:
            raise ValueError("scheduler_grid_minutes must be >= 1")
        for task in request.tasks:
            if task.required_duration_minutes < 1:
                raise ValueError(f"Task {task.id} has invalid duration")
            if task.earliest_start >= task.latest_end:
                raise ValueError(f"Task {task.id}: earliest_start must be before latest_end")
