"""Device form parsing and validation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DeviceCreateForm(BaseModel):
    """Validated form input for creating a new device."""

    name: str = Field(min_length=1, max_length=255)
    device_type: str
    rated_power_w: float = Field(gt=0)
    interruptibility: str = "non_interruptible"
    notes: str = ""
