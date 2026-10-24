"""MyGrid ModuleTwo battery over local Modbus TCP."""

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, HomeAssistantError
from homeassistant.helpers import config_validation as cv

from mygrid_modbus import UNIT_ID, MyGridDevice

from .connection import create_modbus_params
from .const import DOMAIN
from .coordinator import ModuleTwoConfigEntry, ModuleTwoCoordinator
from .helpers import async_reload_entry

MODULETWO_PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.BUTTON,
]


async def async_setup_entry(hass: HomeAssistant, entry: ModuleTwoConfigEntry) -> bool:
    """Validate one real snapshot before setting up entities."""
    try:
        unit = async_get_unit(hass, entry, create_modbus_params(entry.data), UNIT_ID)
    except HomeAssistantError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="link_settings_in_use"
        ) from err
    device = MyGridDevice(unit)
    coordinator = entry.runtime_data = ModuleTwoCoordinator(hass, entry, device)
    await coordinator.async_config_entry_first_refresh()
    # The Modbus manager releases its hold on unload, including setup failure.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, MODULETWO_PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ModuleTwoConfigEntry) -> bool:
    """Unload entities; the Modbus manager releases this entry's connection hold."""
    return await hass.config_entries.async_unload_platforms(entry, MODULETWO_PLATFORMS)


CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)
