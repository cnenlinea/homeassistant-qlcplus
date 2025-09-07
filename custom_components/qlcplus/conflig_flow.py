"""Config flow for QLC+ integration."""

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .api import QLCPlusAPI, QLCPlusAuthError, QLCPlusConnectionError
from .const import DEFAULT_PORT, DOMAIN, LOGGER


class QLCPlusConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for QLC+."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.host = None
        self.username = None
        self.password = None
        self.port = DEFAULT_PORT
        self.api = None
        self._config_data = {}

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult | None:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self.host = user_input["host"]
            self.port = user_input.get("port", DEFAULT_PORT)
            self.username = user_input.get("username")
            self.password = user_input.get("password")

            await self.async_set_unique_id(self.host)
            self._abort_if_unique_id_configured()

            try:
                self.api = QLCPlusAPI(
                    host=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                )
                await self.api.connect()
                self._config_data = user_input
                return await self.async_step_widgets()
            except QLCPlusAuthError:
                errors["base"] = "invalid_auth"
            except QLCPlusConnectionError:
                errors["base"] = "cannot_connect"
            except Exception as exc:
                LOGGER.exception("Unexpected exception: %s", exc)
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_NAME): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_USERNAME): str,
                vol.Optional(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    async def async_step_widgets(
        self, user_input: dict | None = None
    ) -> ConfigFlowResult:
        """Handle the widgets selection step."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._config_data["name"],
                data=self._config_data,
                options=user_input,
            )

        try:
            widgets = await self.api.get_list_of_widgets()
            await self.api.disconnect()
        except QLCPlusConnectionError:
            return self.async_abort(reason="cannot_connect")

        options_schema = vol.Schema(
            {vol.Optional("selected_widgets"): cv.multi_select(widgets)}
        )

        return self.async_show_form(
            step_id="widgets", data_schema=options_schema, last_step=True
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> "QLCPlusOptionsFlowHandler":
        """Create the options flow."""
        return QLCPlusOptionsFlowHandler(config_entry)


class QLCPlusOptionsFlowHandler(OptionsFlow):
    """Handle QLC+ options."""

    def __init__(self, config_entry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """Manage the options step."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        api = self.hass.data[self.config_entry.entry_id].api

        try:
            widgets = await api.get_list_of_widgets()
        except QLCPlusConnectionError:
            return self.async_abort(reason="cannot_connect")

        current_options = self.config_entry.options.get(
            "selected_widgets",
        )

        options_schema_with_cv = vol.Schema(
            {
                vol.Optional(
                    "selected_widgets", default=current_options
                ): cv.multi_select(widgets)
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema_with_cv)
