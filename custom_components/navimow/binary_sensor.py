from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .const import DOMAIN
from .entity import NavimowEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]
    async_add_entities([NavimowCloudConnection(coordinator, d) for d in devices])

class NavimowCloudConnection(NavimowEntity, BinarySensorEntity):
    """Whether Home Assistant can reach the Segway cloud.

    Deliberately not "is the mower switched on": getVehicleStatus keeps serving
    the last known state for a powered-off mower (verified over an hour of
    polling), so that question cannot be answered from this API.
    """

    _attr_translation_key = "cloud_connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, device_data):
        # Suffix kept as "connectivity" so existing entity ids survive the rename
        super().__init__(coordinator, device_data, "connectivity")

    @property
    def available(self) -> bool:
        # Reporting a failed poll is this entity's job, so it never goes unavailable
        return True

    @property
    def is_on(self):
        return self.coordinator.last_update_success
