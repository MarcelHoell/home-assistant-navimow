"""Shared base for all Navimow entities."""
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, is_online


class NavimowEntity(CoordinatorEntity):
    """Wires an entity to its device and to the mower's reachability."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, device_data, unique_id_suffix: str = ""):
        super().__init__(coordinator)
        self._id = device_data.get("id")
        self._attr_unique_id = f"{self._id}_{unique_id_suffix}" if unique_id_suffix else self._id
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self._id)})

    @property
    def status(self) -> dict:
        """This device's slice of the coordinator payload."""
        return self.coordinator.data.get(self._id) or {}

    @property
    def available(self) -> bool:
        """An offline mower reports nothing useful, so say unavailable."""
        return super().available and is_online(self.coordinator.data.get(self._id))
