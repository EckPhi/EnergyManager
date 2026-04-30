"""Pricing domain entities (provider-facing and scheduler-facing)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class IntervalType(str, Enum):
    """How price intervals are structured by the provider."""

    fixed_minutes = "fixed_minutes"
    day_night = "day_night"
    custom_block = "custom_block"
    provider_defined = "provider_defined"


@dataclass
class PricePoint:
    """A single provider-native price interval."""

    interval_start: datetime
    interval_end: datetime
    price_per_kwh: float
    currency: str
    market_timezone: str
    source_provider: str
    source_region: str
    tax_included: bool = False
    quality_flag: str = "ok"
    interval_type: IntervalType = IntervalType.provider_defined
    labels: dict[str, str] = field(default_factory=dict)

    @property
    def duration_minutes(self) -> float:
        """Duration of this price point in minutes."""
        return (self.interval_end - self.interval_start).total_seconds() / 60


@dataclass
class PriceSeries:
    """A sequence of provider-native price points for a day/region."""

    provider: str
    region: str
    fetched_at: datetime
    valid_from: datetime
    valid_to: datetime
    native_resolution_minutes: int
    interval_type: IntervalType
    is_complete: bool
    points: list[PricePoint] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ConversionPolicy(str, Enum):
    """How to handle intervals that don't align with the scheduler grid."""

    strict_fail = "strict_fail"
    forward_fill_with_flag = "forward_fill_with_flag"
    proportional_expand = "proportional_expand"


@dataclass
class SchedulerPricePoint:
    """A single scheduler-ready price interval, aligned to the scheduler grid."""

    interval_start: datetime
    interval_end: datetime
    price_per_kwh: float
    currency: str
    quality_flag: str = "ok"
    was_interpolated: bool = False
    source_interval_start: datetime | None = None
    source_interval_end: datetime | None = None


@dataclass
class SchedulerPriceSeries:
    """Scheduler-ready price series, produced exclusively by PriceTransformationService.

    The optimizer MUST only consume this type, never PriceSeries.
    """

    provider: str
    region: str
    grid_minutes: int
    valid_from: datetime
    valid_to: datetime
    currency: str
    conversion_policy: ConversionPolicy
    points: list[SchedulerPricePoint] = field(default_factory=list)
    conversion_trace: list[str] = field(default_factory=list)
    is_complete: bool = True


class PriceProvider(str, Enum):
    """Known price providers."""

    nordpool = "nordpool"
    awattar = "awattar"


class TariffRegion(str, Enum):
    """Common tariff regions."""

    AT = "AT"
    DE = "DE"
    NO = "NO"
    SE = "SE"
    FI = "FI"
    DK = "DK"
