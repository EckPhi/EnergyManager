"""Nord Pool price provider adapter."""

from __future__ import annotations

from datetime import date, datetime, timezone

import httpx

from energy_scheduler.pricing.contracts import (
    IntervalType,
    PricePoint,
    PriceSeries,
    ProviderCapabilities,
    ProviderConfig,
)


class NordPoolAdapter:
    """Fetches day-ahead prices from the Nord Pool public API."""

    _BASE_URL = "https://dataportal-api.nordpoolgroup.com/api"

    def describe_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="nordpool",
            supported_regions=["AT", "NO1", "NO2", "SE1", "SE2", "FI", "DK1", "DK2"],
            native_resolution_minutes=60,
            supports_day_ahead=True,
            supports_historical=True,
            requires_api_key=False,
            interval_type=IntervalType.fixed_minutes,
        )

    def list_regions(self) -> list[str]:
        return self.describe_capabilities().supported_regions

    async def fetch_day_ahead(self, config: ProviderConfig, target_date: date) -> PriceSeries:
        """Fetch hourly day-ahead prices from Nord Pool for a given date and region."""
        date_str = target_date.strftime("%Y-%m-%d")
        url = f"{self._BASE_URL}/DayAheadPrices"
        params = {
            "date": date_str,
            "market": "DayAhead",
            "deliveryArea": config.region,
            "currency": "EUR",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data, config, target_date)

    async def fetch_historical(
        self, config: ProviderConfig, start: date, end: date
    ) -> list[PriceSeries]:
        results: list[PriceSeries] = []
        current = start
        from datetime import timedelta
        while current <= end:
            try:
                series = await self.fetch_day_ahead(config, current)
                results.append(series)
            except Exception:
                pass
            current += timedelta(days=1)
        return results

    def validate_config(self, config: ProviderConfig) -> list[str]:
        errors: list[str] = []
        if config.region not in self.list_regions():
            errors.append(f"Unsupported region: {config.region}")
        return errors

    def _parse_response(self, data: dict, config: ProviderConfig, target_date: date) -> PriceSeries:
        from datetime import timedelta

        points: list[PricePoint] = []
        now = datetime.now(timezone.utc)
        raw_entries = data.get("multiAreaEntries", [])
        for entry in raw_entries:
            delivery_start = datetime.fromisoformat(entry["deliveryStart"].replace("Z", "+00:00"))
            delivery_end = datetime.fromisoformat(entry["deliveryEnd"].replace("Z", "+00:00"))
            area_prices = entry.get("entryPerArea", {})
            price_eur_mwh = area_prices.get(config.region)
            if price_eur_mwh is None:
                continue
            points.append(
                PricePoint(
                    interval_start=delivery_start,
                    interval_end=delivery_end,
                    price_per_kwh=float(price_eur_mwh) / 1000.0,
                    currency="EUR",
                    market_timezone="Europe/Oslo",
                    source_provider="nordpool",
                    source_region=config.region,
                    interval_type=IntervalType.fixed_minutes,
                )
            )

        day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)

        return PriceSeries(
            provider="nordpool",
            region=config.region,
            fetched_at=now,
            valid_from=day_start,
            valid_to=day_end,
            native_resolution_minutes=60,
            interval_type=IntervalType.fixed_minutes,
            is_complete=len(points) == 24,
            points=points,
        )
