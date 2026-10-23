"""Privacy-preserving diagnostics without network requests."""

from dataclasses import asdict
from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import MyGridConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MyGridConfigEntry
) -> dict[str, Any]:
    """Use an allowlist so hosts, names and entry identifiers never escape."""
    coordinator = entry.runtime_data
    return {
        "options": dict(entry.options),
        "last_update_success": coordinator.last_update_success,
        "data": asdict(coordinator.data),
        "active_faults": coordinator.data.active_faults,
    }
