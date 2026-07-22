from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .const import DOMAIN, is_online
from .entity import NavimowEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]
    async_add_entities([NavimowConnectivity(coordinator, d) for d in devices])

class NavimowConnectivity(NavimowEntity, BinarySensorEntity):
    _attr_translation_key = "connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, device_data):
        super().__init__(coordinator, device_data, "connectivity")

    @property
    def available(self) -> bool:
        # Reporting the mower as offline is this entity's job, so it stays
        # available as long as the coordinator itself is healthy.
        return self.coordinator.last_update_success

    @property
    def is_on(self):
        return is_online(self.coordinator.data.get(self._id))
