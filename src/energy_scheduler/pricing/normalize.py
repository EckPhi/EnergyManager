"""Raw payload cleanup, interval repair, and DST handling."""

from __future__ import annotations

import zoneinfo
from datetime import datetime, timedelta, timezone

from energy_scheduler.pricing.contracts import IntervalType, PricePoint, PriceSeries


def normalize_series(series: PriceSeries, tz_name: str = "UTC") -> PriceSeries:
    """Normalise a raw PriceSeries: sort, repair gaps, and attach timezone info.

    Args:
        series: The provider-native series to normalise.
        tz_name: IANA timezone name used for gap detection and DST handling.

    Returns:
        A new PriceSeries with sorted, timezone-aware, gap-repaired points.
    """
    tz = zoneinfo.ZoneInfo(tz_name)
    points = [_ensure_aware(pt, tz) for pt in series.points]
    points.sort(key=lambda p: p.interval_start)
    points = _repair_gaps(points, series.native_resolution_minutes)
    return PriceSeries(
        provider=series.provider,
        region=series.region,
        fetched_at=series.fetched_at,
        valid_from=series.valid_from,
        valid_to=series.valid_to,
        native_resolution_minutes=series.native_resolution_minutes,
        interval_type=series.interval_type,
        is_complete=_check_completeness(points, series.valid_from, series.valid_to, series.native_resolution_minutes),
        points=points,
        metadata=dict(series.metadata),
    )


def _ensure_aware(pt: PricePoint, tz: zoneinfo.ZoneInfo) -> PricePoint:
    start = pt.interval_start if pt.interval_start.tzinfo else pt.interval_start.replace(tzinfo=tz)
    end = pt.interval_end if pt.interval_end.tzinfo else pt.interval_end.replace(tzinfo=tz)
    return PricePoint(
        interval_start=start,
        interval_end=end,
        price_per_kwh=pt.price_per_kwh,
        currency=pt.currency,
        market_timezone=pt.market_timezone or tz.key,
        source_provider=pt.source_provider,
        source_region=pt.source_region,
        tax_included=pt.tax_included,
        quality_flag=pt.quality_flag,
        interval_type=pt.interval_type,
        labels=dict(pt.labels),
    )


def _repair_gaps(points: list[PricePoint], resolution_minutes: int) -> list[PricePoint]:
    """Forward-fill missing intervals, flagging them as interpolated."""
    if not points:
        return points
    repaired: list[PricePoint] = [points[0]]
    step = timedelta(minutes=resolution_minutes)
    for current in points[1:]:
        prev = repaired[-1]
        expected_start = prev.interval_end
        # Fill any gap between expected_start and current.interval_start
        while current.interval_start - expected_start > timedelta(seconds=30):
            fill = PricePoint(
                interval_start=expected_start,
                interval_end=expected_start + step,
                price_per_kwh=prev.price_per_kwh,
                currency=prev.currency,
                market_timezone=prev.market_timezone,
                source_provider=prev.source_provider,
                source_region=prev.source_region,
                tax_included=prev.tax_included,
                quality_flag="gap_filled",
                interval_type=prev.interval_type,
            )
            repaired.append(fill)
            expected_start = fill.interval_end
        repaired.append(current)
    return repaired


def _check_completeness(
    points: list[PricePoint],
    valid_from: datetime,
    valid_to: datetime,
    resolution_minutes: int,
) -> bool:
    if not points:
        return False
    expected = int((valid_to - valid_from).total_seconds() / 60 / resolution_minutes)
    return len(points) >= expected
