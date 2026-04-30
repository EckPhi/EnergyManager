"""Pricing contracts: provider capabilities and runtime configuration.

Scheduler-facing types (SchedulerPriceSeries, SchedulerPricePoint, ConversionPolicy)
and shared primitives (IntervalType, PricePoint, PriceSeries) are defined in
energy_scheduler.domain.pricing and re-exported here for convenience.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Re-export domain types so existing callers of pricing.contracts keep working.
from energy_scheduler.domain.pricing import (
    ConversionPolicy,
    IntervalType,
    PricePoint,
    PriceSeries,
    SchedulerPricePoint,
    SchedulerPriceSeries,
)

__all__ = [
    "ConversionPolicy",
    "IntervalType",
    "PricePoint",
    "PriceSeries",
    "ProviderCapabilities",
    "ProviderConfig",
    "SchedulerPricePoint",
    "SchedulerPriceSeries",
]


@dataclass
class ProviderCapabilities:
    """Describes what a provider adapter can do."""

    provider_name: str
    supported_regions: list[str]
    native_resolution_minutes: int
    supports_day_ahead: bool
    supports_historical: bool
    requires_api_key: bool
    interval_type: IntervalType = IntervalType.provider_defined
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConfig:
    """Runtime configuration for a provider adapter."""

    provider_name: str
    region: str
    api_key: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)
