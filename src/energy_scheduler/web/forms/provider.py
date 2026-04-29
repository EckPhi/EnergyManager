"""Provider form parsing and validation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProviderConfigForm(BaseModel):
    """Validated form input for configuring a price provider."""

    provider_name: str
    region: str
    api_key: str | None = None
