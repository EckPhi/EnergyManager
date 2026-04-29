"""Retraining and backfill jobs for the forecasting service."""

from __future__ import annotations

from uuid import UUID


async def retrain_device_profiles(device_ids: list[UUID] | None = None) -> None:
    """Retrain consumption profiles from stored observations.

    Args:
        device_ids: Specific devices to retrain, or None for all.
    """
    # TODO: load observations from DB and call ForecastingService.train()
    print(f"[forecasting_job] Retraining profiles for devices: {device_ids or 'all'}")


async def backfill_observations(days: int = 30) -> None:
    """Backfill historical consumption observations from device logs."""
    print(f"[forecasting_job] Backfilling {days} days of observations")
