"""MyGrid ModuleTwo local Modbus TCP integration."""

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from mygrid_modbus import MyGridClient, MyGridError, UnsupportedMapError

from .const import DOMAIN
from .coordinator import MyGridConfigEntry, MyGridCoordinator

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.NUMBER, Platform.BUTTON]
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: MyGridConfigEntry) -> bool:
    """Validate one real snapshot before setting up entities."""
    client = MyGridClient(entry.data[CONF_HOST], entry.data[CONF_PORT])
    try:
        data = await client.async_read()
    except UnsupportedMapError as err:
        await client.async_close()
        raise ConfigEntryError(
            translation_domain=DOMAIN, translation_key="unsupported_map"
        ) from err
    except MyGridError as err:
        await client.async_close()
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN, translation_key="communication_error"
        ) from err

    coordinator = entry.runtime_data = MyGridCoordinator(hass, entry, client)
    coordinator.async_set_updated_data(data)
    # Also runs if setup of a platform fails, not just on a normal unload.
    entry.async_on_unload(client.async_close)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_reload_entry(hass: HomeAssistant, entry: MyGridConfigEntry) -> None:
    """Apply polling options through a clean reload."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: MyGridConfigEntry) -> bool:
    """Unload entities and close the owned TCP connection."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
