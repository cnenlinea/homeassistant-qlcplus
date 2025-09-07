"""Switch platform for QLC+ integration."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
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
    """Set up the QLC+ select platform."""
    coordinator = hass.data[entry.entry_id]

    selected_widget_ids = entry.options.get("selected_widgets", [])

    if not selected_widget_ids:
        entities = [
            QLCPlusSwitchEntity(coordinator, entry, widget)
            for widget in coordinator.data.values()
        ]
    else:
        entities = [
            QLCPlusSwitchEntity(coordinator, entry, widget)
            for widget in coordinator.data.values()
            if widget["id"] in selected_widget_ids
        ]

    async_add_entities(entities)


class QLCPlusSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Representation of a QLC+ widget."""

    def __init__(
        self,
        coordinator: QLCPlusDataUpdateCoordinator,
        entry: ConfigEntry,
        widget: dict,
    ) -> None:
        """Initialize the switch entity."""
        super().__init__(coordinator)
        self.widget_id = widget["id"]
        self._entry = entry
        self._attr_unique_id = f"{entry.unique_id}_{self.widget_id}"
        self._attr_name = f"{entry.title} {widget['name']}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.unique_id)}, name=self._entry.title
        )

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        await super().async_added_to_hass()
        if self.coordinator.data:
            self._attr_is_on = (
                self.coordinator.data.get(
                    self.widget_id, {}).get("status") == "255"
            )
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self.coordinator.data:
            self._attr_is_on = (
                self.coordinator.data.get(
                    self.widget_id, {}).get("status") == "255"
            )
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the switch on."""
        await self.coordinator.api.set_widget_value(self.widget_id, 255)
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the switch off."""
        await self.coordinator.api.set_widget_value(self.widget_id, 255)
        self._attr_is_on = False
        self.async_write_ha_state()
