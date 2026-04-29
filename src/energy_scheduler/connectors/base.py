"""Connector Protocol — the interface every device connector must implement."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class DeviceConnector(Protocol):
    """Protocol for device integration adapters."""

    async def discover(self) -> list[dict[str, Any]]:
        """Discover available devices/entities from the integration.

        Returns:
            List of entity descriptor dicts (integration-specific format).
        """
        ...

    async def bind(self, external_entity_id: str) -> dict[str, Any]:
        """Bind to a specific entity and return its current state.

        Args:
            external_entity_id: Integration-specific entity identifier.
        """
        ...

    async def execute_command(
        self,
        external_entity_id: str,
        command: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a command to a device entity.

        Args:
            external_entity_id: Target entity.
            command: Command name (e.g. 'turn_on', 'set_delay').
            params: Optional command parameters.
        """
        ...

    async def poll_state(self, external_entity_id: str) -> dict[str, Any]:
        """Poll the current state of a device entity."""
        ...

    def report_capabilities(self) -> dict[str, Any]:
        """Return static capability metadata for this connector."""
        ...
