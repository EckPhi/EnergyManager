"""Pricing domain entities (provider-facing)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
    metadata: dict[str, object] = field(default_factory=dict)


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
