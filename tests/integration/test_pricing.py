"""Integration tests for provider behavior (mocked HTTP)."""

from __future__ import annotations

from datetime import date

import httpx
import pytest
import respx

from energy_scheduler.pricing.contracts import ProviderConfig
from energy_scheduler.pricing.providers.awattar import AWattarAdapter


class TestAWattarIntegration:
    async def test_fetch_day_ahead_returns_series(self, respx_mock: respx.MockRouter) -> None:
        target = date(2024, 1, 15)
        data = {
            "data": [
                {
                    "start_timestamp": 1705276800000,
                    "end_timestamp": 1705280400000,
                    "marketprice": 50.0,
                }
                for _ in range(24)
            ]
        }
        respx_mock.get("https://api.awattar.at/v1/marketdata").mock(
            return_value=httpx.Response(200, json=data)
        )
        adapter = AWattarAdapter()
        config = ProviderConfig(provider_name="awattar", region="at")
        series = await adapter.fetch_day_ahead(config, target)
        assert series.provider == "awattar"
        assert len(series.points) == 24
        assert all(abs(pt.price_per_kwh - 0.05) < 1e-6 for pt in series.points)

    def test_validate_config_valid(self) -> None:
        adapter = AWattarAdapter()
        errors = adapter.validate_config(ProviderConfig(provider_name="awattar", region="at"))
        assert errors == []

    def test_validate_config_invalid_region(self) -> None:
        adapter = AWattarAdapter()
        errors = adapter.validate_config(ProviderConfig(provider_name="awattar", region="XX"))
        assert len(errors) > 0
