from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity

from .const import DOMAIN
from .entity import NavimowEntity

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]
    async_add_entities([NavimowTracker(coordinator, d) for d in devices])

class NavimowTracker(NavimowEntity, TrackerEntity):
    _attr_translation_key = "position"

    def __init__(self, coordinator, device_data):
        super().__init__(coordinator, device_data, "tracker")

    @property
    def latitude(self):
        pos = self.status.get("position")
        return pos.get("lat") if pos else None

    @property
    def longitude(self):
        pos = self.status.get("position")
        return pos.get("lng") if pos else None

    @property
    def source_type(self):
        return SourceType.GPS
