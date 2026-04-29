"""Tests for Home Assistant connector with mocked responses."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
import respx
import httpx

from energy_scheduler.connectors.home_assistant import HomeAssistantConnector


HA_URL = "http://homeassistant.local:8123"
TOKEN = "test-token"


@pytest.fixture()
def connector() -> HomeAssistantConnector:
    return HomeAssistantConnector(base_url=HA_URL, token=TOKEN)


class TestDiscover:
    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_entity_list(self, connector: HomeAssistantConnector) -> None:
        respx.get(f"{HA_URL}/api/states").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {"entity_id": "switch.washing_machine", "state": "off", "attributes": {}},
                    {"entity_id": "switch.dishwasher", "state": "off", "attributes": {}},
                ],
            )
        )
        entities = await connector.discover()
        assert len(entities) == 2
        assert entities[0]["entity_id"] == "switch.washing_machine"

    @pytest.mark.asyncio
    @respx.mock
    async def test_http_error_propagates(self, connector: HomeAssistantConnector) -> None:
        respx.get(f"{HA_URL}/api/states").mock(return_value=httpx.Response(401))
        with pytest.raises(httpx.HTTPStatusError):
            await connector.discover()


class TestExecuteCommand:
    @pytest.mark.asyncio
    @respx.mock
    async def test_turn_on(self, connector: HomeAssistantConnector) -> None:
        respx.post(f"{HA_URL}/api/services/switch/turn_on").mock(
            return_value=httpx.Response(200, json=[])
        )
        result = await connector.execute_command("switch.washing_machine", "turn_on")
        assert result["status"] == "ok"
        assert result["command"] == "turn_on"


class TestPollState:
    @pytest.mark.asyncio
    @respx.mock
    async def test_returns_state_dict(self, connector: HomeAssistantConnector) -> None:
        respx.get(f"{HA_URL}/api/states/switch.washing_machine").mock(
            return_value=httpx.Response(
                200,
                json={
                    "entity_id": "switch.washing_machine",
                    "state": "on",
                    "attributes": {"friendly_name": "Washing Machine"},
                },
            )
        )
        state = await connector.poll_state("switch.washing_machine")
        assert state["state"] == "on"


class TestReportCapabilities:
    def test_capabilities(self, connector: HomeAssistantConnector) -> None:
        caps = connector.report_capabilities()
        assert caps["connector_type"] == "home_assistant"
        assert caps["supports_delayed_start"] is True
