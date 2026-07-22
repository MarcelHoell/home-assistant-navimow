"""Segway Navimow integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .api import NavimowApiClient
from .coordinator import NavimowDataUpdateCoordinator

PLATFORMS = ["lawn_mower", "sensor", "binary_sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up integration from config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    token = entry.data.get("access_token")
    session = async_get_clientsession(hass)
    api_client = NavimowApiClient(token, session)

    devices = await api_client.async_get_devices()
    coordinator = NavimowDataUpdateCoordinator(hass, api_client, entry, devices)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api_client,
        "devices": devices
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Remove integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id)
        await data["coordinator"].async_shutdown()
    return unload_ok