"""Button platform for QLC+ integration."""

from homeassistant.components.button import ButtonEntity
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
    """Set up the QLC+ button entities."""
    reset_desk = QLCPlusResetButtonEntity(
        coordinator=hass.data[entry.entry_id], entry=entry
    )
    stop_functions = QLCPlusStopButtonEntity(
        coordinator=hass.data[entry.entry_id], entry=entry
    )
    async_add_entities([reset_desk, stop_functions], update_before_add=True)


class QLCPlusResetButtonEntity(CoordinatorEntity, ButtonEntity):
    """Representation of the QLC+ reset Simple Desk Button."""

    def __init__(
        self, coordinator: QLCPlusDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the number."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_reset_desk"
        self._attr_name = f"{entry.title} Reset Simple Desk"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id)}, name=self._entry.title
        )

    async def async_press(self) -> None:
        """Reset Simple Desk."""
        await self.coordinator.api.reset_simple_desk()


class QLCPlusStopButtonEntity(CoordinatorEntity, ButtonEntity):
    """Representation of the QLC+ stop functions Button."""

    def __init__(
        self, coordinator: QLCPlusDataUpdateCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_stop_functions"
        self._attr_name = f"{entry.title} Stop All Functions"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id)}, name=self._entry.title
        )

    async def async_press(self) -> None:
        """Stop Functions."""
        await self.coordinator.api.stop_functions()
