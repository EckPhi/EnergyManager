"""Tests for pricing normalizer."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from energy_scheduler.pricing.contracts import IntervalType, PricePoint, PriceSeries
from energy_scheduler.pricing.normalize import normalize_series


def make_series_with_gap() -> PriceSeries:
    """Build a series missing hour 2 (02:00-03:00)."""
    base = datetime(2024, 1, 15, tzinfo=timezone.utc)
    delta = timedelta(hours=1)
    hours_present = list(range(0, 2)) + list(range(3, 6))
    points = [
        PricePoint(
            interval_start=base + delta * h,
            interval_end=base + delta * (h + 1),
            price_per_kwh=0.10,
            currency="EUR",
            market_timezone="Europe/Vienna",
            source_provider="test",
            source_region="AT",
            interval_type=IntervalType.fixed_minutes,
        )
        for h in hours_present
    ]
    return PriceSeries(
        provider="test",
        region="AT",
        fetched_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        valid_from=base,
        valid_to=base + delta * 6,
        native_resolution_minutes=60,
        interval_type=IntervalType.fixed_minutes,
        is_complete=False,
        points=points,
    )


class TestNormalize:
    def test_gap_filled(self) -> None:
        series = make_series_with_gap()
        result = normalize_series(series, tz_name="UTC")
        assert len(result.points) == 6

    def test_gap_flagged(self) -> None:
        series = make_series_with_gap()
        result = normalize_series(series, tz_name="UTC")
        filled = [pt for pt in result.points if pt.quality_flag == "gap_filled"]
        assert len(filled) == 1

    def test_sorted_after_normalize(self) -> None:
        series = make_series_with_gap()
        result = normalize_series(series, tz_name="UTC")
        starts = [pt.interval_start for pt in result.points]
        assert starts == sorted(starts)

    def test_tz_aware_after_normalize(self) -> None:
        base = datetime(2024, 1, 15)  # naive
        delta = timedelta(hours=1)
        points = [
            PricePoint(
                interval_start=base + delta * h,
                interval_end=base + delta * (h + 1),
                price_per_kwh=0.10,
                currency="EUR",
                market_timezone="",
                source_provider="test",
                source_region="AT",
            )
            for h in range(3)
        ]
        series = PriceSeries(
            provider="test",
            region="AT",
            fetched_at=datetime(2024, 1, 15),
            valid_from=base,
            valid_to=base + delta * 3,
            native_resolution_minutes=60,
            interval_type=IntervalType.fixed_minutes,
            is_complete=True,
            points=points,
        )
        result = normalize_series(series, tz_name="Europe/Vienna")
        for pt in result.points:
            assert pt.interval_start.tzinfo is not None
