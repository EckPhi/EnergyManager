"""Tests for PriceTransformationService."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from energy_scheduler.pricing.contracts import (
    ConversionPolicy,
    IntervalType,
    PricePoint,
    PriceSeries,
)
from energy_scheduler.pricing.transform import ConversionError, PriceTransformationService


def make_series(
    start_hour: int,
    n_hours: int,
    resolution_minutes: int = 60,
    price: float = 0.10,
) -> PriceSeries:
    start = datetime(2024, 1, 15, start_hour, tzinfo=timezone.utc)
    delta = timedelta(minutes=resolution_minutes)
    points = []
    for i in range(n_hours):
        slot = start + delta * i
        points.append(
            PricePoint(
                interval_start=slot,
                interval_end=slot + delta,
                price_per_kwh=price,
                currency="EUR",
                market_timezone="Europe/Vienna",
                source_provider="test",
                source_region="AT",
                interval_type=IntervalType.fixed_minutes,
            )
        )
    return PriceSeries(
        provider="test",
        region="AT",
        fetched_at=datetime(2024, 1, 15, tzinfo=timezone.utc),
        valid_from=start,
        valid_to=start + delta * n_hours,
        native_resolution_minutes=resolution_minutes,
        interval_type=IntervalType.fixed_minutes,
        is_complete=True,
        points=points,
    )


class TestHourToQuarterExpansion:
    def test_24_hourly_to_96_quarter_slots(self) -> None:
        series = make_series(0, 24, resolution_minutes=60)
        svc = PriceTransformationService()
        result = svc.transform(series, grid_minutes=15, policy=ConversionPolicy.proportional_expand)
        assert len(result.points) == 96

    def test_prices_preserved_after_expansion(self) -> None:
        series = make_series(0, 1, resolution_minutes=60, price=0.25)
        svc = PriceTransformationService()
        result = svc.transform(series, grid_minutes=15, policy=ConversionPolicy.proportional_expand)
        for pt in result.points:
            assert abs(pt.price_per_kwh - 0.25) < 1e-6

    def test_grid_minutes_preserved(self) -> None:
        series = make_series(0, 24, resolution_minutes=60)
        svc = PriceTransformationService()
        result = svc.transform(series, grid_minutes=15)
        assert result.grid_minutes == 15

    def test_no_duplicate_slots(self) -> None:
        series = make_series(0, 24, resolution_minutes=60)
        svc = PriceTransformationService()
        result = svc.transform(series, grid_minutes=15)
        starts = [pt.interval_start for pt in result.points]
        assert len(starts) == len(set(starts))


class TestAlreadyAligned:
    def test_60min_to_60min_passthrough(self) -> None:
        series = make_series(0, 24, resolution_minutes=60)
        svc = PriceTransformationService()
        result = svc.transform(series, grid_minutes=60)
        assert len(result.points) == 24
        for pt in result.points:
            assert pt.quality_flag == "ok"


class TestStrictFailPolicy:
    def test_strict_fail_raises_on_mismatch(self) -> None:
        series = make_series(0, 24, resolution_minutes=60)
        svc = PriceTransformationService()
        with pytest.raises(ConversionError):
            svc.transform(series, grid_minutes=15, policy=ConversionPolicy.strict_fail)


class TestForwardFillPolicy:
    def test_forward_fill_flags_expanded_slots(self) -> None:
        series = make_series(0, 4, resolution_minutes=60)
        svc = PriceTransformationService()
        result = svc.transform(
            series, grid_minutes=15, policy=ConversionPolicy.forward_fill_with_flag
        )
        assert all(pt.was_interpolated for pt in result.points)


class TestEmptySeries:
    def test_empty_series_returns_empty_result(self) -> None:
        series = make_series(0, 0)
        svc = PriceTransformationService()
        result = svc.transform(series, grid_minutes=15)
        assert result.points == []
        assert not result.is_complete
