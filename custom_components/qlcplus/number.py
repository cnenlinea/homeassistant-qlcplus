"""Number platform for QLC+ integration."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QLCPlusDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the QLC+ number entities."""
    gm_number = QLCPlusGMNumberEntity(
        coordinator=hass.data[entry.entry_id], entry=entry
    ) 
    async_add_entities([gm_number], update_before_add=True)


class QLCPlusGMNumberEntity(CoordinatorEntity, NumberEntity):
    """Representation of the QLC+ GM Slider."""

    def __init__(
        self, coordinator: QLCPlusDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_native_step = 1
        self._attr_unique_id = f"{entry.unique_id}_gm"
        self._attr_name = f"{entry.title} GM"
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_max_value = 255
        self._attr_native_min_value = 0

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id)}, name=self._entry.title
        )

    async def async_set_native_value(self, value: float) -> None:
        """Set GM value."""
        gm_value = int(value)
        await self.coordinator.api.set_gm_value(gm_value)
        self._attr_native_value = gm_value
        self.async_write_ha_state()
