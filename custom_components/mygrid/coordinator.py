"""Single polling coordinator and serialized command publication."""

import logging
from asyncio import Lock
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from mygrid_modbus import BatteryData, InvalidSetpointError, MyGridClient, MyGridError

from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN

LOGGER = logging.getLogger(__name__)
type MyGridConfigEntry = ConfigEntry[MyGridCoordinator]


class MyGridCoordinator(DataUpdateCoordinator[BatteryData]):
    """Publish coherent snapshots and never replay a power command."""

    def __init__(
        self, hass: HomeAssistant, entry: MyGridConfigEntry, client: MyGridClient
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                seconds=entry.options.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
            ),
            always_update=False,
        )
        self.client = client
        self._operation_lock = Lock()

    async def _async_update_data(self) -> BatteryData:
        async with self._operation_lock:
            try:
                return await self.client.async_read()
            except MyGridError as err:
                raise UpdateFailed(
                    translation_domain=DOMAIN, translation_key="communication_error"
                ) from err

    async def async_set_power(self, watts: float) -> None:
        """Write once and publish the readback under the same operation lock."""
        async with self._operation_lock:
            try:
                data = await self.client.async_set_power(watts)
            except InvalidSetpointError as err:
                raise ServiceValidationError(
                    translation_domain=DOMAIN, translation_key="invalid_setpoint"
                ) from err
            except MyGridError as err:
                self.async_set_update_error(UpdateFailed("Command confirmation failed"))
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="command_failed"
                ) from err
            self.async_set_updated_data(data)

    async def async_restart(self) -> None:
        """Request restart and immediately invalidate cached telemetry."""
        async with self._operation_lock:
            try:
                await self.client.async_restart()
            except MyGridError as err:
                self.async_set_update_error(UpdateFailed("Restart confirmation failed"))
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="command_failed"
                ) from err
            self.async_set_update_error(UpdateFailed("Battery restart requested"))
            await self.client.async_close()
