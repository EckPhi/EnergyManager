"""PriceProviderAdapter Protocol — the interface every provider must implement."""

from __future__ import annotations

from datetime import date
from typing import Protocol, runtime_checkable

from energy_scheduler.pricing.contracts import (
    ProviderCapabilities,
    ProviderConfig,
    PriceSeries,
)


@runtime_checkable
class PriceProviderAdapter(Protocol):
    """Protocol for all price provider adapters."""

    def describe_capabilities(self) -> ProviderCapabilities:
        """Return static capability metadata for this provider."""
        ...

    def list_regions(self) -> list[str]:
        """Return the list of supported region codes."""
        ...

    async def fetch_day_ahead(self, config: ProviderConfig, target_date: date) -> PriceSeries:
        """Fetch day-ahead prices for the given date and region.

        Args:
            config: Provider configuration including region and credentials.
            target_date: The calendar date for which to fetch prices.

        Returns:
            Provider-native PriceSeries (not yet scheduler-ready).
        """
        ...

    async def fetch_historical(
        self,
        config: ProviderConfig,
        start: date,
        end: date,
    ) -> list[PriceSeries]:
        """Fetch historical price series for a date range.

        Args:
            config: Provider configuration.
            start: Start date (inclusive).
            end: End date (inclusive).

        Returns:
            List of provider-native PriceSeries, one per day.
        """
        ...

    def validate_config(self, config: ProviderConfig) -> list[str]:
        """Validate the provider config and return a list of error messages (empty = ok)."""
        ...
