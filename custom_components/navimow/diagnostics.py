"""Diagnostics support for the Navimow integration."""
from homeassistant.components.diagnostics import async_redact_data

from .const import DOMAIN

TO_REDACT = {"access_token", "refresh_token", "pwdInfo", "userName", "sn", "deviceSn"}


async def async_get_config_entry_diagnostics(hass, entry) -> dict:
    """Dump entry, device list and coordinator data with secrets removed."""
    stored = hass.data[DOMAIN][entry.entry_id]
    coordinator = stored["coordinator"]

    return async_redact_data(
        {
            "entry_data": dict(entry.data),
            "devices": stored["devices"],
            "coordinator_data": coordinator.data,
            "mqtt_connected": coordinator._mqtt_client is not None,
        },
        TO_REDACT,
    )
