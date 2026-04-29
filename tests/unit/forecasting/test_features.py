"""Tests for feature extraction."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from energy_scheduler.domain.forecasting import ConsumptionObservation
from energy_scheduler.forecasting.features import extract_profiles


def make_obs(device_id, duration_minutes: int, energy_kwh: float) -> ConsumptionObservation:
    return ConsumptionObservation(
        device_id=device_id,
        observed_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration_minutes=duration_minutes,
        energy_kwh=energy_kwh,
    )


class TestExtractProfiles:
    def test_single_device(self) -> None:
        device_id = uuid4()
        obs = [make_obs(device_id, 90, 2.5), make_obs(device_id, 70, 1.8)]
        profiles = extract_profiles(obs)
        assert device_id in profiles
        p = profiles[device_id]
        assert p.sample_count == 2
        assert abs(p.mean_duration_minutes - 80.0) < 0.001
        assert abs(p.mean_energy_kwh - 2.15) < 0.001

    def test_multiple_devices(self) -> None:
        d1, d2 = uuid4(), uuid4()
        obs = [make_obs(d1, 60, 1.0), make_obs(d2, 120, 3.0)]
        profiles = extract_profiles(obs)
        assert d1 in profiles
        assert d2 in profiles

    def test_single_observation_stddev_zero(self) -> None:
        device_id = uuid4()
        obs = [make_obs(device_id, 90, 2.5)]
        profiles = extract_profiles(obs)
        assert profiles[device_id].stddev_duration_minutes == 0.0

    def test_percentiles_computed(self) -> None:
        device_id = uuid4()
        obs = [make_obs(device_id, d, e) for d, e in [(60, 1.0), (90, 2.0), (120, 3.0)]]
        profiles = extract_profiles(obs)
        p = profiles[device_id]
        assert "p50" in p.percentiles
        assert "p90" in p.percentiles
        assert p.percentiles["p50"] <= p.percentiles["p90"]

    def test_empty_observations(self) -> None:
        assert extract_profiles([]) == {}
