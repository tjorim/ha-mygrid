"""Home Assistant integration fixtures."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mygrid.client import MyGridClient, decode_registers
from custom_components.mygrid.const import DOMAIN


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations) -> None:
    """Enable local integrations without installing requirements per test."""


@pytest.fixture
def registers() -> list[int]:
    """Map includes negative power, high words and a high fault bit."""
    return [2, 82, 65528, 12, 10, 64736, 0, 0, 0, 0, 3000, 0, 7, 2, 9, 3, 5000, 0]


@pytest.fixture
def mock_client(registers: list[int]) -> Generator[AsyncMock]:
    """Mock the network boundary, retaining real platform code."""
    client = AsyncMock(spec=MyGridClient)
    client.async_read.return_value = decode_registers(registers)
    client.async_set_power.return_value = decode_registers(registers)
    with (
        patch("custom_components.mygrid.MyGridClient", return_value=client),
        patch("custom_components.mygrid.config_flow.MyGridClient", return_value=client),
    ):
        yield client


@pytest.fixture
def entry() -> MockConfigEntry:
    """Persistent identity does not depend on the network address."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="MyGrid ModuleTwo",
        unique_id="persistent-identity",
        data={"host": "battery.local", "port": 502},
    )
