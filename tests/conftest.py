"""Integration fixtures mock the independent device API, not the protocol."""

from collections.abc import Callable, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from modbus_connection.model import UpdateReport
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mygrid.const import DOMAIN
from custom_components.mygrid.vendor.mygrid_modbus import BatteryData, MyGridDevice
from custom_components.mygrid.vendor.mygrid_voltbridge import P1Broadcast

from .voltbridge_support import SERIAL, make_data, make_telegram


@pytest.fixture
def registers() -> list[int]:
    return [2, 82, 65528, 12, 10, 64736, 0, 0, 0, 0, 3000, 0, 7, 2, 9, 3, 5000, 0]


@pytest.fixture
def mock_client(registers: list[int]) -> Generator[AsyncMock]:
    device = AsyncMock(spec=MyGridDevice)
    device.snapshot = BatteryData(
        2, 82, -800, 1200, 1000, -800, 0, 0, 3000, 131079, 196617, 5000
    )
    device.async_read.return_value = device.snapshot
    device.async_update.return_value = UpdateReport(updated={"battery"})
    device.async_set_power.return_value = device.snapshot
    device.async_read_raw.return_value = {"holding": dict(enumerate(registers))}

    async def confirm(value):
        device.snapshot = device.async_set_power.return_value
        return device.snapshot

    device.async_set_power.side_effect = confirm
    with (
        patch("custom_components.mygrid.MyGridDevice", return_value=device),
        patch(
            "custom_components.mygrid.config_flow.MyGridDevice",
            return_value=device,
        ),
    ):
        yield device


@pytest.fixture
def entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="MyGrid ModuleTwo",
        unique_id="persistent-identity",
        data={"host": "battery.local", "port": 502},
    )


async def start_moduletwo(hass, data=None):
    """Open the user menu, choose the ModuleTwo, and optionally submit its form."""
    from homeassistant.config_entries import SOURCE_USER
    from homeassistant.data_entry_flow import FlowResultType

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "moduletwo"}
    )
    if data is not None:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    return result


@pytest.fixture
def vb_client() -> Generator[AsyncMock]:
    with (
        patch(
            "custom_components.mygrid.voltbridge_coordinator.VoltBridgeClient"
        ) as coordinator_cls,
        patch(
            "custom_components.mygrid.config_flow.VoltBridgeClient",
            coordinator_cls,
        ),
    ):
        instance = AsyncMock()
        instance.async_get_p1_data.return_value = make_data()
        instance.async_get_telegram.return_value = make_telegram()
        coordinator_cls.return_value = instance
        yield instance


@pytest.fixture
def vb_listener() -> Generator[Callable[[], Callable[[P1Broadcast], None]]]:
    """Patch ``async_listen``; the returned getter yields the registered callback."""
    transport = MagicMock()
    with patch(
        "custom_components.mygrid.voltbridge_coordinator.async_listen",
        new_callable=AsyncMock,
        return_value=transport,
    ) as listen:
        listen.transport = transport
        yield lambda: listen.call_args.args[0]


@pytest.fixture
def vb_entry() -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="MyGrid VoltBridge",
        unique_id=SERIAL,
        data={"device": "voltbridge", "host": "192.168.0.45"},
    )


@pytest.fixture
def vb_setup_entry() -> Generator[None]:
    """Skip real setup when a flow creates an entry."""
    with patch("custom_components.mygrid.async_setup_entry", return_value=True):
        yield


async def start_voltbridge(hass, data=None):
    """Open the user menu, choose the VoltBridge, and optionally submit its form."""
    from homeassistant.config_entries import SOURCE_USER
    from homeassistant.data_entry_flow import FlowResultType

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.MENU
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "voltbridge"}
    )
    if data is not None:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], data)
    return result


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    """Enable the generated custom integration in the test runtime."""
