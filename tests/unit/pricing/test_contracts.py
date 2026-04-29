"""Tests for PricePoint, PriceSeries, and IntervalType contracts."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from energy_scheduler.pricing.contracts import (
    ConversionPolicy,
    IntervalType,
    PricePoint,
    PriceSeries,
    ProviderCapabilities,
    SchedulerPriceSeries,
)


def make_point(start_hour: int, duration_h: int = 1, price: float = 0.10) -> PricePoint:
    start = datetime(2024, 1, 15, start_hour, tzinfo=timezone.utc)
    from datetime import timedelta
    return PricePoint(
        interval_start=start,
        interval_end=start + timedelta(hours=duration_h),
        price_per_kwh=price,
        currency="EUR",
        market_timezone="Europe/Vienna",
        source_provider="test",
        source_region="AT",
    )


class TestIntervalType:
    def test_all_values_are_strings(self) -> None:
        for member in IntervalType:
            assert isinstance(member.value, str)

    def test_specific_values(self) -> None:
        assert IntervalType.fixed_minutes == "fixed_minutes"
        assert IntervalType.day_night == "day_night"
        assert IntervalType.custom_block == "custom_block"
        assert IntervalType.provider_defined == "provider_defined"


class TestPricePoint:
    def test_duration_minutes(self) -> None:
        pt = make_point(0, duration_h=1)
        assert pt.duration_minutes == 60.0

    def test_fractional_duration(self) -> None:
        from datetime import timedelta
        start = datetime(2024, 1, 15, 0, tzinfo=timezone.utc)
        pt = PricePoint(
            interval_start=start,
            interval_end=start + timedelta(minutes=15),
            price_per_kwh=0.05,
            currency="EUR",
            market_timezone="UTC",
            source_provider="test",
            source_region="AT",
        )
        assert pt.duration_minutes == 15.0

    def test_default_quality_flag(self) -> None:
        pt = make_point(0)
        assert pt.quality_flag == "ok"

    def test_default_interval_type(self) -> None:
        pt = make_point(0)
        assert pt.interval_type == IntervalType.provider_defined


class TestPriceSeries:
    def test_empty_series(self) -> None:
        series = PriceSeries(
            provider="test",
            region="AT",
            fetched_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            valid_from=datetime(2024, 1, 15, tzinfo=timezone.utc),
            valid_to=datetime(2024, 1, 16, tzinfo=timezone.utc),
            native_resolution_minutes=60,
            interval_type=IntervalType.fixed_minutes,
            is_complete=False,
        )
        assert series.points == []
        assert series.metadata == {}

    def test_series_with_points(self) -> None:
        points = [make_point(h) for h in range(24)]
        series = PriceSeries(
            provider="test",
            region="AT",
            fetched_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
            valid_from=datetime(2024, 1, 15, tzinfo=timezone.utc),
            valid_to=datetime(2024, 1, 16, tzinfo=timezone.utc),
            native_resolution_minutes=60,
            interval_type=IntervalType.fixed_minutes,
            is_complete=True,
            points=points,
        )
        assert len(series.points) == 24
        assert series.is_complete


class TestConversionPolicy:
    def test_all_values(self) -> None:
        assert ConversionPolicy.strict_fail == "strict_fail"
        assert ConversionPolicy.forward_fill_with_flag == "forward_fill_with_flag"
        assert ConversionPolicy.proportional_expand == "proportional_expand"
