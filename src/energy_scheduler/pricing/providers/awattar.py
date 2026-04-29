"""aWATTar price provider adapter."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import httpx

from energy_scheduler.pricing.contracts import (
    IntervalType,
    PricePoint,
    PriceSeries,
    ProviderCapabilities,
    ProviderConfig,
)


class AWattarAdapter:
    """Fetches hourly spot prices from the aWATTar public API."""

    _BASE_URLS = {
        "at": "https://api.awattar.at/v1",
        "de": "https://api.awattar.de/v1",
    }

    def describe_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="awattar",
            supported_regions=["at", "de"],
            native_resolution_minutes=60,
            supports_day_ahead=True,
            supports_historical=True,
            requires_api_key=False,
            interval_type=IntervalType.fixed_minutes,
        )

    def list_regions(self) -> list[str]:
        return list(self._BASE_URLS)

    async def fetch_day_ahead(self, config: ProviderConfig, target_date: date) -> PriceSeries:
        """Fetch hourly prices from aWATTar for a given date."""
        country = config.region.lower()
        base_url = self._BASE_URLS.get(country, self._BASE_URLS["at"])
        day_start = datetime(target_date.year, target_date.month, target_date.day, tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        params = {
            "start": int(day_start.timestamp() * 1000),
            "end": int(day_end.timestamp() * 1000),
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{base_url}/marketdata", params=params)
            response.raise_for_status()
            data = response.json()

        return self._parse_response(data, config, day_start, day_end)

    async def fetch_historical(
        self, config: ProviderConfig, start: date, end: date
    ) -> list[PriceSeries]:
        results: list[PriceSeries] = []
        current = start
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
        if config.region.lower() not in self.list_regions():
            errors.append(f"Unsupported region: {config.region}")
        return errors

    def _parse_response(
        self,
        data: dict,
        config: ProviderConfig,
        day_start: datetime,
        day_end: datetime,
    ) -> PriceSeries:
        points: list[PricePoint] = []
        now = datetime.now(timezone.utc)
        for entry in data.get("data", []):
            start_ms = entry.get("start_timestamp", 0)
            end_ms = entry.get("end_timestamp", 0)
            price_eur_mwh = entry.get("marketprice", 0.0)
            interval_start = datetime.fromtimestamp(start_ms / 1000, tz=timezone.utc)
            interval_end = datetime.fromtimestamp(end_ms / 1000, tz=timezone.utc)
            points.append(
                PricePoint(
                    interval_start=interval_start,
                    interval_end=interval_end,
                    price_per_kwh=float(price_eur_mwh) / 1000.0,
                    currency="EUR",
                    market_timezone="Europe/Vienna",
                    source_provider="awattar",
                    source_region=config.region,
                    interval_type=IntervalType.fixed_minutes,
                )
            )
        return PriceSeries(
            provider="awattar",
            region=config.region,
            fetched_at=now,
            valid_from=day_start,
            valid_to=day_end,
            native_resolution_minutes=60,
            interval_type=IntervalType.fixed_minutes,
            is_complete=len(points) == 24,
            points=points,
        )
