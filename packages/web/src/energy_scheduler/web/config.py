"""Application configuration via Pydantic Settings."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration, sourced from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./energy_scheduler.db",
        description="SQLAlchemy async database URL",
    )

    # Application
    secret_key: str = Field(default="dev-secret-key-change-me")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Timezone
    timezone: str = Field(default="Europe/Vienna", description="IANA timezone name")

    # Scheduler
    scheduler_grid_minutes: int = Field(
        default=15,
        ge=1,
        le=60,
        description="Default scheduling grid resolution in minutes",
    )

    # Pricing
    price_provider: str = Field(default="awattar", description="Active price provider name")

    # Nord Pool
    nordpool_region: str = Field(default="AT")
    nordpool_api_key: str | None = Field(default=None)

    # aWATTar
    awattar_country: str = Field(default="at")
    awattar_api_key: str | None = Field(default=None)

    # Home Assistant
    home_assistant_url: str = Field(default="http://homeassistant.local:8123")
    home_assistant_token: str = Field(default="")


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
