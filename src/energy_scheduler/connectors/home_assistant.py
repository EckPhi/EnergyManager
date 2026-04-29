"""Home Assistant connector adapter."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx


class HomeAssistantConnector:
    """Connects to Home Assistant via its REST API and WebSocket."""

    def __init__(self, base_url: str, token: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=self._base_url, headers=self._headers, timeout=10.0)

    async def discover(self) -> list[dict[str, Any]]:
        """List all entities from Home Assistant."""
        async with self._client() as client:
            response = await client.get("/api/states")
            response.raise_for_status()
            states: list[dict[str, Any]] = response.json()
        return [
            {
                "entity_id": s["entity_id"],
                "state": s.get("state"),
                "attributes": s.get("attributes", {}),
            }
            for s in states
        ]

    async def bind(self, external_entity_id: str) -> dict[str, Any]:
        """Return current state for a specific entity."""
        return await self.poll_state(external_entity_id)

    async def execute_command(
        self,
        external_entity_id: str,
        command: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a service call to Home Assistant.

        Args:
            external_entity_id: The HA entity_id (e.g. 'switch.washing_machine').
            command: HA service name (e.g. 'turn_on', 'turn_off').
            params: Additional service data.
        """
        domain, _ = external_entity_id.split(".", 1)
        service_data: dict[str, Any] = {"entity_id": external_entity_id}
        if params:
            service_data.update(params)
        async with self._client() as client:
            response = await client.post(
                f"/api/services/{domain}/{command}",
                json=service_data,
            )
            response.raise_for_status()
            return {"status": "ok", "command": command, "entity_id": external_entity_id}

    async def poll_state(self, external_entity_id: str) -> dict[str, Any]:
        """Fetch the current state of an entity."""
        async with self._client() as client:
            response = await client.get(f"/api/states/{external_entity_id}")
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        return data

    async def delayed_start(
        self,
        external_entity_id: str,
        start_at: datetime,
    ) -> dict[str, Any]:
        """Schedule a delayed turn-on for a device via an automation or script.

        Args:
            external_entity_id: The HA entity_id.
            start_at: UTC datetime when the device should turn on.
        """
        return await self.execute_command(
            external_entity_id,
            "turn_on",
            params={"scheduled_time": start_at.isoformat()},
        )

    def report_capabilities(self) -> dict[str, Any]:
        return {
            "connector_type": "home_assistant",
            "supports_delayed_start": True,
            "supports_pause_resume": False,
            "base_url": self._base_url,
        }
