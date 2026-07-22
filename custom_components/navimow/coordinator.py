"""DataUpdateCoordinator for Segway Navimow integration."""
from datetime import timedelta
import logging
import time

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class NavimowDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator for centralized data fetching and token refresh."""

    def __init__(self, hass, api, entry, devices):
        """Initialize coordinator."""
        self.api = api
        self.entry = entry
        self.devices = devices
        self._token_expires_at = 0  # Timestamp when access token expires

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_ensure_valid_token(self, force: bool = False) -> bool:
        """Refresh the OAuth token if it expired or is about to.

        The single place that refreshes tokens. `force` skips the expiry check
        for the reactive path, where the server already told us the token is
        dead. Returns True when a usable token is in place.
        """
        now = time.time()
        if not force and now < self._token_expires_at - 10:
            return True  # Token still valid, no need to refresh

        refresh_token = self.entry.data.get("refresh_token")
        if not refresh_token:
            return False

        try:
            token_response = await self.api.async_refresh_token(refresh_token)
        except Exception as err:
            _LOGGER.warning("Failed to refresh OAuth token: %s", err)
            return False

        if not token_response or "access_token" not in token_response:
            _LOGGER.error("Refresh token is invalid or server rejected the request")
            return False

        new_access = token_response["access_token"]
        expires_in = token_response.get("expires_in", 3600)  # Default 1 hour if not provided
        self._token_expires_at = now + expires_in
        self.api._token = new_access

        self.hass.config_entries.async_update_entry(
            self.entry,
            data={
                **self.entry.data,
                "access_token": new_access,
                "refresh_token": token_response.get("refresh_token", refresh_token),
            },
        )
        _LOGGER.debug("OAuth token refreshed (expires in %ds)", expires_in)
        return True

    async def _async_update_data(self):
        """Fetch vehicle data and handle token refresh."""
        await self._async_ensure_valid_token()

        device_ids = [d["id"] for d in self.devices]

        if not device_ids:
            _LOGGER.debug("No devices found for this account")
            return {}

        data = await self.api.async_get_all_vehicles_status(device_ids)

        if isinstance(data, dict) and data.get("error") == "TOKEN_EXPIRED":
            _LOGGER.info("Access token expired, attempting refresh...")
            if not await self._async_ensure_valid_token(force=True):
                # Triggers the reauth flow, which keeps the entry and its entity ids
                raise ConfigEntryAuthFailed("Navimow session expired")
            data = await self.api.async_get_all_vehicles_status(device_ids)

        if data is None or (isinstance(data, dict) and data.get("error")):
            raise UpdateFailed("Communication error with Navimow servers")

        return data
