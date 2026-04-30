"""Periodic provider price sync jobs."""

from __future__ import annotations

import asyncio
from datetime import date

from energy_scheduler.pricing.contracts import ConversionPolicy, ProviderConfig


async def sync_prices_for_today(
    provider_name: str,
    config: ProviderConfig,
    grid_minutes: int = 15,
) -> None:
    """Fetch and store today's prices from the configured provider.

    This job is idempotent: re-running it updates the cached series.
    """
    from energy_scheduler.pricing.registry import get_registry
    from energy_scheduler.pricing.transform import PriceTransformationService

    registry = get_registry()
    adapter = registry.get(provider_name)
    today = date.today()
    series = await adapter.fetch_day_ahead(config, today)
    transform = PriceTransformationService()
    scheduler_series = transform.transform(series, grid_minutes=grid_minutes, policy=ConversionPolicy.proportional_expand)
    # TODO: persist scheduler_series to the database
    print(f"[prices_job] Synced {len(scheduler_series.points)} slots for {today}")


def run_sync_job(provider_name: str, region: str) -> None:
    """Synchronous entry point for a cron runner."""
    config = ProviderConfig(provider_name=provider_name, region=region)
    asyncio.run(sync_prices_for_today(provider_name, config))
