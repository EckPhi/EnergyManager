"""Active provider selection and fetch orchestration."""

from __future__ import annotations

from datetime import date

from energy_scheduler.domain.pricing import ConversionPolicy, PriceSeries, SchedulerPriceSeries
from energy_scheduler.pricing.contracts import ProviderConfig
from energy_scheduler.pricing.registry import ProviderRegistry
from energy_scheduler.pricing.transform import PriceTransformationService


class PricingService:
    """Orchestrates provider selection, fetching, and transformation."""

    def __init__(
        self,
        registry: ProviderRegistry,
        transformation_service: PriceTransformationService | None = None,
    ) -> None:
        self._registry = registry
        self._transform = transformation_service or PriceTransformationService()

    async def fetch_day_ahead(
        self,
        provider_name: str,
        config: ProviderConfig,
        target_date: date,
    ) -> PriceSeries:
        """Fetch provider-native day-ahead prices."""
        adapter = self._registry.get(provider_name)
        return await adapter.fetch_day_ahead(config, target_date)

    async def fetch_and_transform(
        self,
        provider_name: str,
        config: ProviderConfig,
        target_date: date,
        grid_minutes: int = 15,
        policy: ConversionPolicy = ConversionPolicy.proportional_expand,
    ) -> SchedulerPriceSeries:
        """Fetch prices and transform them to a scheduler-ready series."""
        series = await self.fetch_day_ahead(provider_name, config, target_date)
        return self._transform.transform(series, grid_minutes=grid_minutes, policy=policy)
