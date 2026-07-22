from homeassistant.components.lawn_mower import LawnMowerEntity, LawnMowerEntityFeature, LawnMowerActivity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo
import logging

from .const import DOMAIN
from .entity import NavimowEntity

_LOGGER = logging.getLogger(__name__)

RAW_STATE_TO_CANONICAL = {
    "isDocked": "docked",
    "isIdel": "offline",  # see OFFLINE_RAW_STATES in const.py: this is a powered-off mower
    "isIdle": "idle",
    "isMapping": "mowing",
    "isRunning": "mowing",
    "isPaused": "paused",
    "isDocking": "returning",
    "Error": "error",
    "error": "error",
    "isLifted": "error",
    "inSoftwareUpdate": "paused",
    "Self-Checking": "idle",
    "Self-checking": "idle",
    "Offline": "offline",
    "offline": "offline",
}

CANONICAL_TO_ACTIVITY = {
    "mowing": LawnMowerActivity.MOWING,
    "returning": LawnMowerActivity.RETURNING,
    "paused": LawnMowerActivity.PAUSED,
    "error": LawnMowerActivity.ERROR,
    "docked": LawnMowerActivity.DOCKED,
    # ponytail: no IDLE member in LawnMowerActivity, DOCKED is the closest
    "idle": LawnMowerActivity.DOCKED,
    # "offline" has no activity on purpose: the entity reports unavailable
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]
    async_add_entities([NavimowLawnMower(coordinator, d) for d in devices])

class NavimowLawnMower(NavimowEntity, LawnMowerEntity):
    _attr_name = None  # the mower entity carries the device name itself
    _attr_supported_features = (
        LawnMowerEntityFeature.START_MOWING | LawnMowerEntityFeature.PAUSE | LawnMowerEntityFeature.DOCK
    )

    def __init__(self, coordinator, device_data):
        super().__init__(coordinator, device_data)
        self._api = coordinator.api

        # Only the mower entity names the device, the others just attach to it
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._id)},
            name=device_data.get("name"),
            manufacturer="Segway",
            model=device_data.get("model"),
            # authList calls it "firmware", not "firmware_version"
            sw_version=device_data.get("firmware"),
        )

    @property
    def activity(self) -> LawnMowerActivity | None:
        """Get current mowing activity state."""
        raw_state = self.status.get("vehicleState")
        canonical = RAW_STATE_TO_CANONICAL.get(raw_state, "unknown")
        activity = CANONICAL_TO_ACTIVITY.get(canonical)
        if activity is None:
            # Unknown raw state: say so instead of claiming it is parked
            _LOGGER.debug("Unmapped vehicleState %r for device %s", raw_state, self._id)
        return activity

    async def _async_send_command(self, command: str, params: dict = None, label: str = "") -> None:
        """Send command to device with proactive token refresh.

        Ensures OAuth token is valid before sending the command to avoid
        CODE_OAUTH_INFO_ILLEGAL errors when token has expired. Raises on a
        rejected command so the failure surfaces in the UI instead of being
        logged as a success.
        """
        if not await self.coordinator._async_ensure_valid_token():
            raise HomeAssistantError("Navimow session expired, please re-authenticate")

        try:
            res = await self._api.async_send_command(self._id, command, params)
        except Exception as err:
            raise HomeAssistantError(f"Could not reach Navimow servers: {err}") from err

        if res.get("code") != 1:
            raise HomeAssistantError(
                f"Navimow rejected {command}: {res.get('desc') or res.get('code')}"
            )

        if label:
            _LOGGER.info("%s for device %s", label, self._id)
        await self.coordinator.async_request_refresh()

    async def async_start_mowing(self):
        raw_state = self.status.get("vehicleState")
        if RAW_STATE_TO_CANONICAL.get(raw_state) == "paused":
            # Resuming needs PauseUnpause, StartStop would restart the job
            await self._async_send_command(
                "action.devices.commands.PauseUnpause", {"on": True}, "Resumed mowing"
            )
        else:
            await self._async_send_command(
                "action.devices.commands.StartStop", {"on": True}, "Started mowing"
            )

    async def async_pause(self):
        await self._async_send_command(
            "action.devices.commands.PauseUnpause", {"on": False}, "Paused mowing"
        )

    async def async_dock(self):
        await self._async_send_command("action.devices.commands.Dock", None, "Docked")
