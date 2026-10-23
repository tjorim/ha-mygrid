"""Real sockets exercise pymodbus framing, response handling and reconnects."""

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType

from custom_components.mygrid.const import DOMAIN
from tests.simulator import BatterySimulator

pytestmark = [pytest.mark.simulator, pytest.mark.usefixtures("socket_enabled")]


async def test_home_assistant_end_to_end(hass, registers):
    async with BatterySimulator(registers) as battery:
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={"host": "127.0.0.1", "port": battery.port},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        await hass.async_block_till_done()
        entry = result["result"]
        assert entry.runtime_data.data.state_of_charge == 82
        assert battery.writes == []
        await entry.runtime_data.async_set_power(-500)
        assert entry.runtime_data.data.setpoint == -500
        assert battery.writes == [(2, 65531)]
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert battery.maximum_connections == 1
        assert battery.rejects == 0
        assert battery.writes == [(2, 65531)]
