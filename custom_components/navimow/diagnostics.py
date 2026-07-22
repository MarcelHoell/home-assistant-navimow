"""Diagnostics support for the Navimow integration."""
from homeassistant.components.diagnostics import async_redact_data

from .const import DOMAIN

# "id" is the mower's serial number, so it goes too
TO_REDACT = {"access_token", "refresh_token", "pwdInfo", "userName", "id", "sn", "deviceSn"}


async def async_get_config_entry_diagnostics(hass, entry) -> dict:
    """Dump entry, device list and coordinator data with secrets removed."""
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = stored["coordinator"]

    return async_redact_data(
        {
            "entry_data": dict(entry.data),
            "devices": stored["devices"],
            # Listed, not keyed by device id — the key would leak the serial
            "coordinator_data": list((coordinator.data or {}).values()),
        },
        TO_REDACT,
    )
