from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE

from .const import DOMAIN
from .entity import NavimowEntity

_ERROR_RAW_STATES = {"Error", "error", "isLifted"}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    devices = hass.data[DOMAIN][entry.entry_id]["devices"]
    async_add_entities(
        [NavimowBattery(coordinator, d) for d in devices]
        + [NavimowErrorSensor(coordinator, d) for d in devices]
    )

class NavimowBattery(NavimowEntity, SensorEntity):
    _attr_translation_key = "battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, device_data):
        super().__init__(coordinator, device_data, "battery")

    @property
    def native_value(self):
        cap = self.status.get("capacityRemaining", [{}])
        return cap[0].get("rawValue") if cap else None

    @property
    def extra_state_attributes(self):
        """Segway's own wording for the charge level, e.g. "FULL"."""
        descriptive = self.status.get("descriptiveCapacityRemaining")
        return {"descriptive_capacity": descriptive} if descriptive else None


class NavimowErrorSensor(NavimowEntity, SensorEntity):
    _attr_translation_key = "error"
    _attr_icon = "mdi:alert-circle"

    def __init__(self, coordinator, device_data):
        super().__init__(coordinator, device_data, "error")

    @property
    def native_value(self):
        error_code = self.status.get("error_code")
        if error_code and error_code != "none":
            return error_code
        if self.status.get("vehicleState") in _ERROR_RAW_STATES:
            return self.status.get("vehicleState")
        return "none"
