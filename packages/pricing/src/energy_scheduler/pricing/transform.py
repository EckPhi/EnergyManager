"""PriceTransformationService: converts provider-native PriceSeries to SchedulerPriceSeries."""

from __future__ import annotations

from datetime import datetime, timedelta

from energy_scheduler.domain.pricing import (
    ConversionPolicy,
    PriceSeries,
    SchedulerPricePoint,
    SchedulerPriceSeries,
)


class ConversionError(Exception):
    """Raised when strict_fail policy encounters incompatible intervals."""


class PriceTransformationService:
    """Transforms provider-native PriceSeries into scheduler-ready SchedulerPriceSeries.

    The scheduler MUST only consume SchedulerPriceSeries produced by this service.
    """

    def transform(
        self,
        series: PriceSeries,
        grid_minutes: int = 15,
        policy: ConversionPolicy = ConversionPolicy.proportional_expand,
    ) -> SchedulerPriceSeries:
        """Convert a PriceSeries to a SchedulerPriceSeries aligned to the given grid.

        Args:
            series: Provider-native price series.
            grid_minutes: Target scheduler grid resolution in minutes.
            policy: How to handle misaligned intervals.

        Returns:
            Scheduler-ready SchedulerPriceSeries.

        Raises:
            ConversionError: When policy is strict_fail and intervals don't align.
        """
        trace: list[str] = []
        grid_delta = timedelta(minutes=grid_minutes)

        if not series.points:
            return SchedulerPriceSeries(
                provider=series.provider,
                region=series.region,
                grid_minutes=grid_minutes,
                valid_from=series.valid_from,
                valid_to=series.valid_to,
                currency="",
                conversion_policy=policy,
                points=[],
                conversion_trace=["empty_series"],
                is_complete=False,
            )

        currency = series.points[0].currency
        scheduler_points: list[SchedulerPricePoint] = []

        for pt in series.points:
            source_duration = (pt.interval_end - pt.interval_start).total_seconds() / 60
            if abs(source_duration - grid_minutes) < 0.5:
                # Perfect alignment
                scheduler_points.append(
                    SchedulerPricePoint(
                        interval_start=pt.interval_start,
                        interval_end=pt.interval_end,
                        price_per_kwh=pt.price_per_kwh,
                        currency=pt.currency,
                        quality_flag=pt.quality_flag,
                        source_interval_start=pt.interval_start,
                        source_interval_end=pt.interval_end,
                    )
                )
            elif source_duration > grid_minutes:
                # Source interval longer than grid: expand into sub-intervals
                if policy == ConversionPolicy.strict_fail:
                    raise ConversionError(
                        f"Source interval {source_duration}min > grid {grid_minutes}min at {pt.interval_start}"
                    )
                slots = self._expand_interval(pt, grid_delta, policy, trace)
                scheduler_points.extend(slots)
            else:
                # Source interval shorter than grid
                if policy == ConversionPolicy.strict_fail:
                    raise ConversionError(
                        f"Source interval {source_duration}min < grid {grid_minutes}min at {pt.interval_start}"
                    )
                # For sub-grid intervals, use proportional or forward-fill: snap to grid boundary
                snapped_start = self._snap_to_grid(pt.interval_start, grid_delta)
                snapped_end = snapped_start + grid_delta
                flag = "sub_grid_expanded" if policy == ConversionPolicy.forward_fill_with_flag else "ok"
                existing = next(
                    (sp for sp in scheduler_points if sp.interval_start == snapped_start), None
                )
                if existing is None:
                    scheduler_points.append(
                        SchedulerPricePoint(
                            interval_start=snapped_start,
                            interval_end=snapped_end,
                            price_per_kwh=pt.price_per_kwh,
                            currency=pt.currency,
                            quality_flag=flag,
                            was_interpolated=(policy == ConversionPolicy.forward_fill_with_flag),
                            source_interval_start=pt.interval_start,
                            source_interval_end=pt.interval_end,
                        )
                    )
                    trace.append(f"sub_grid_snap:{pt.interval_start.isoformat()}")

        scheduler_points.sort(key=lambda p: p.interval_start)
        scheduler_points = self._deduplicate(scheduler_points)

        return SchedulerPriceSeries(
            provider=series.provider,
            region=series.region,
            grid_minutes=grid_minutes,
            valid_from=series.valid_from,
            valid_to=series.valid_to,
            currency=currency,
            conversion_policy=policy,
            points=scheduler_points,
            conversion_trace=trace,
            is_complete=series.is_complete,
        )

    def _expand_interval(
        self,
        pt: object,
        grid_delta: timedelta,
        policy: ConversionPolicy,
        trace: list[str],
    ) -> list[SchedulerPricePoint]:
        """Expand a long provider interval into multiple grid-aligned sub-intervals."""
        from energy_scheduler.domain.pricing import PricePoint

        assert isinstance(pt, PricePoint)
        result: list[SchedulerPricePoint] = []
        current = self._snap_to_grid(pt.interval_start, grid_delta)
        flag = "expanded" if policy == ConversionPolicy.forward_fill_with_flag else "ok"

        while current < pt.interval_end:
            slot_end = current + grid_delta
            result.append(
                SchedulerPricePoint(
                    interval_start=current,
                    interval_end=slot_end,
                    price_per_kwh=pt.price_per_kwh,
                    currency=pt.currency,
                    quality_flag=flag,
                    was_interpolated=(policy == ConversionPolicy.forward_fill_with_flag),
                    source_interval_start=pt.interval_start,
                    source_interval_end=pt.interval_end,
                )
            )
            current = slot_end

        if result:
            trace.append(f"expanded:{pt.interval_start.isoformat()}:{len(result)}_slots")
        return result

    @staticmethod
    def _snap_to_grid(dt: datetime, grid_delta: timedelta) -> datetime:
        """Snap a datetime down to the nearest grid boundary."""
        epoch = datetime(dt.year, dt.month, dt.day, tzinfo=dt.tzinfo)
        offset = (dt - epoch).total_seconds()
        grid_secs = grid_delta.total_seconds()
        snapped_offset = (offset // grid_secs) * grid_secs
        return epoch + timedelta(seconds=snapped_offset)

    @staticmethod
    def _deduplicate(points: list[SchedulerPricePoint]) -> list[SchedulerPricePoint]:
        """Remove duplicate grid slots, keeping the first occurrence."""
        seen: set[datetime] = set()
        result: list[SchedulerPricePoint] = []
        for pt in points:
            if pt.interval_start not in seen:
                seen.add(pt.interval_start)
                result.append(pt)
        return result
