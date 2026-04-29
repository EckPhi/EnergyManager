"""Provider registry and capability lookup."""

from __future__ import annotations

from energy_scheduler.pricing.base import PriceProviderAdapter
from energy_scheduler.pricing.contracts import ProviderCapabilities


class ProviderRegistry:
    """Registry of available price provider adapters."""

    def __init__(self) -> None:
        self._providers: dict[str, PriceProviderAdapter] = {}

    def register(self, name: str, adapter: PriceProviderAdapter) -> None:
        """Register a provider adapter under a given name."""
        self._providers[name] = adapter

    def get(self, name: str) -> PriceProviderAdapter:
        """Retrieve a registered adapter by name.

        Raises:
            KeyError: If the provider is not registered.
        """
        if name not in self._providers:
            raise KeyError(f"Price provider '{name}' is not registered. Available: {list(self._providers)}")
        return self._providers[name]

    def list_providers(self) -> list[str]:
        """Return sorted list of registered provider names."""
        return sorted(self._providers)

    def capabilities(self, name: str) -> ProviderCapabilities:
        """Return capability metadata for a named provider."""
        return self.get(name).describe_capabilities()


_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    """Return the global provider registry, initialised on first call."""
    global _registry
    if _registry is None:
        from energy_scheduler.pricing.providers.nordpool import NordPoolAdapter
        from energy_scheduler.pricing.providers.awattar import AWattarAdapter

        _registry = ProviderRegistry()
        _registry.register("nordpool", NordPoolAdapter())
        _registry.register("awattar", AWattarAdapter())
    return _registry
