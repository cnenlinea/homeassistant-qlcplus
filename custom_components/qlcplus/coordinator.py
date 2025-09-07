"""DataUpdateCoordinator for QLC+ integration."""

from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import QLCPlusAPI, QLCPlusAuthError, QLCPlusConnectionError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, LOGGER


class QLCPlusDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching QLC+ data."""

    def __init__(self, hass, api: QLCPlusAPI) -> None:
        """Initialize the coordinator."""
        self.api = api
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from QLC+."""
        try:
            widgets = await self.api.get_list_of_widgets()
            data = {}
            for widget_id, widget_name in widgets.items():
                widget_status = await self.api.get_widget_status(widget_id)
                data[widget_id] = {
                    "id": widget_id,
                    "name": widget_name,
                    "status": widget_status,
                }
        except QLCPlusAuthError as exc:
            raise UpdateFailed("Authentication error") from exc
        except QLCPlusConnectionError as exc:
            raise UpdateFailed("Connection error") from exc
        except Exception as exc:
            LOGGER.exception("Unexpected error: %s", exc)
            raise UpdateFailed("An unknown error occurred") from exc

        return data
