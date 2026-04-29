"""Explanation payload generation for schedule results."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from energy_scheduler.pricing.contracts import SchedulerPriceSeries
from energy_scheduler.scheduling.models import ScheduleItem, ScheduleResult


@dataclass
class ScheduleExplanation:
    """Human-readable explanation for a scheduling decision."""

    item: ScheduleItem
    selected_window_start: datetime
    selected_window_end: datetime
    estimated_cost_eur: float | None
    avoided_peak_slots: list[datetime] = field(default_factory=list)
    delay_reason: str = ""
    cheapest_available_price: float | None = None
    most_expensive_avoided_price: float | None = None


def explain_result(
    result: ScheduleResult,
    price_series: SchedulerPriceSeries | None = None,
) -> list[ScheduleExplanation]:
    """Generate explanations for each scheduled item.

    Args:
        result: The schedule result to explain.
        price_series: Optional scheduler-ready price series for cost context.

    Returns:
        List of ScheduleExplanation objects.
    """
    price_map: dict[datetime, float] = {}
    if price_series is not None:
        for pt in price_series.points:
            price_map[pt.interval_start] = pt.price_per_kwh

    explanations: list[ScheduleExplanation] = []
    for item in result.items:
        avoided = [
            slot
            for slot in price_map
            if slot not in item.slots_used
            and price_map[slot] > (price_map.get(item.slots_used[0], 0.0) if item.slots_used else 0.0)
        ]
        cheapest = min(price_map.values(), default=None)
        most_expensive_avoided = max((price_map[s] for s in avoided), default=None)

        explanations.append(
            ScheduleExplanation(
                item=item,
                selected_window_start=item.start_at,
                selected_window_end=item.end_at,
                estimated_cost_eur=item.estimated_cost_eur,
                avoided_peak_slots=avoided,
                cheapest_available_price=cheapest,
                most_expensive_avoided_price=most_expensive_avoided,
            )
        )

    for task_id in result.unschedulable_task_ids:
        explanations.append(
            ScheduleExplanation(
                item=ScheduleItem(
                    task_id=task_id,
                    device_id=task_id,
                    start_at=datetime.utcnow(),
                    end_at=datetime.utcnow(),
                ),
                selected_window_start=datetime.utcnow(),
                selected_window_end=datetime.utcnow(),
                estimated_cost_eur=None,
                delay_reason="no_feasible_window",
            )
        )

    return explanations
