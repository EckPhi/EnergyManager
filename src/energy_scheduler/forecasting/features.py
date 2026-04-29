"""Historical feature extraction from device run observations."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from energy_scheduler.domain.forecasting import ConsumptionObservation, ConsumptionProfile


def extract_profiles(
    observations: list[ConsumptionObservation],
) -> dict[UUID, ConsumptionProfile]:
    """Aggregate observations into per-device consumption profiles.

    Args:
        observations: List of raw consumption observations.

    Returns:
        Dict mapping device_id to its ConsumptionProfile.
    """
    by_device: dict[UUID, list[ConsumptionObservation]] = defaultdict(list)
    for obs in observations:
        by_device[obs.device_id].append(obs)

    profiles: dict[UUID, ConsumptionProfile] = {}
    for device_id, obs_list in by_device.items():
        durations = [o.duration_minutes for o in obs_list]
        energies = [o.energy_kwh for o in obs_list]
        n = len(obs_list)
        mean_dur = sum(durations) / n
        mean_en = sum(energies) / n
        std_dur = _stddev(durations, mean_dur)
        std_en = _stddev(energies, mean_en)

        # Compute basic percentiles
        sorted_en = sorted(energies)
        p50 = _percentile(sorted_en, 50)
        p90 = _percentile(sorted_en, 90)

        profiles[device_id] = ConsumptionProfile(
            device_id=device_id,
            mean_duration_minutes=mean_dur,
            mean_energy_kwh=mean_en,
            sample_count=n,
            computed_at=datetime.now(timezone.utc),
            stddev_duration_minutes=std_dur,
            stddev_energy_kwh=std_en,
            percentiles={"p50": p50, "p90": p90},
        )
    return profiles


def _stddev(values: list[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


def _percentile(sorted_values: list[float], pct: int) -> float:
    if not sorted_values:
        return 0.0
    idx = (pct / 100) * (len(sorted_values) - 1)
    lower = int(idx)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = idx - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction
