"""QLC+ Integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .api import QLCPlusAPI
from .const import DOMAIN, PLATFORMS, SERVICE_SEND_COMMAND
from .coordinator import QLCPlusDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up QLC+ from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data["host"]
    port = entry.data.get("port")
    username = entry.data.get("username")
    password = entry.data.get("password")

    api = QLCPlusAPI(host=host, port=port,
                     username=username, password=password)

    coordinator = QLCPlusDataUpdateCoordinator(hass, api)

    await coordinator.async_config_entry_first_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def send_command_service(call: ServiceCall) -> SupportsResponse | None:
        """Handle the service call to send a command to QLC+."""
        command = call.data.get("command")
        devices = call.data.get("device_id", [])

        device_reg = dr.async_get(hass)
        for device_id in devices:
            device = device_reg.async_get(device_id)
            if device:
                for config_entry_id in device.config_entries:
                    if config_entry_id in hass.data:
                        target_coordinator = hass.data[config_entry_id]
                        response = await target_coordinator.api.send_command_and_wait_for_response(
                            command
                        )
                        return {"response": response}
        return {"response": "No valid device found."}

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_COMMAND,
        send_command_service,
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(entry.entry_id)

    if not hass.data:
        hass.services.async_remove(DOMAIN, SERVICE_SEND_COMMAND)

    return unload_ok
