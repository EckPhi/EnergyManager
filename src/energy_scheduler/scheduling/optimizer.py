"""Solver selection and optimization orchestration.

Uses OR-Tools CP-SAT if available; falls back to the greedy heuristic.
This module is deliberately isolated from connectors, pricing providers, and web.
"""

from __future__ import annotations

from energy_scheduler.scheduling.heuristics import GreedyHeuristicPlanner
from energy_scheduler.scheduling.models import ScheduleRequest, ScheduleResult


class SchedulerOptimizer:
    """Selects the best available solver and runs the optimization.

    Currently implements the greedy heuristic as the primary solver.
    OR-Tools CP-SAT integration is stubbed for future use.
    """

    def __init__(self, prefer_solver: str = "auto") -> None:
        self._prefer_solver = prefer_solver
        self._heuristic = GreedyHeuristicPlanner()

    def solve(self, request: ScheduleRequest) -> ScheduleResult:
        """Run the optimizer on the scheduling request.

        Args:
            request: The scheduling request with tasks and prices.

        Returns:
            ScheduleResult from the best available solver.
        """
        if self._prefer_solver == "ortools":
            return self._try_ortools(request)
        return self._heuristic.solve(request)

    def _try_ortools(self, request: ScheduleRequest) -> ScheduleResult:
        """Attempt CP-SAT solve; fall back to heuristic if OR-Tools unavailable."""
        try:
            from ortools.sat.python import cp_model  # type: ignore[import]

            return self._solve_cp_sat(request, cp_model)
        except ImportError:
            result = self._heuristic.solve(request)
            result.solver_notes = "ortools_unavailable_fallback_to_heuristic"
            return result

    def _solve_cp_sat(self, request: ScheduleRequest, cp_model: object) -> ScheduleResult:
        """CP-SAT implementation stub — to be completed when OR-Tools is added."""
        # TODO: implement CP-SAT model when or-tools is added as a dependency
        result = self._heuristic.solve(request)
        result.solver = "cp_sat_stub_fallback"
        return result
