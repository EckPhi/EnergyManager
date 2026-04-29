"""Training/prediction orchestration with a replaceable service boundary."""

from __future__ import annotations

from uuid import UUID

from energy_scheduler.domain.forecasting import ConsumptionObservation, ConsumptionProfile
from energy_scheduler.forecasting.features import extract_profiles


class ForecastingService:
    """Coordinates consumption profile extraction and prediction.

    This service defines the boundary for ML model integration.
    Replace or extend the predict method to plug in a trained model.
    """

    def __init__(self) -> None:
        self._profiles: dict[UUID, ConsumptionProfile] = {}

    def train(self, observations: list[ConsumptionObservation]) -> None:
        """Update consumption profiles from new observations."""
        self._profiles.update(extract_profiles(observations))

    def get_profile(self, device_id: UUID) -> ConsumptionProfile | None:
        """Return the current profile for a device, or None if not enough data."""
        return self._profiles.get(device_id)

    def predict_duration_minutes(self, device_id: UUID) -> float | None:
        """Predict expected run duration for the next task.

        Returns the mean duration from the consumption profile, or None.
        """
        profile = self._profiles.get(device_id)
        if profile is None:
            return None
        return profile.mean_duration_minutes
