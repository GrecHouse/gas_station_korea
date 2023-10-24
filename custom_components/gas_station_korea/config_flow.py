"""Config flow for Gas Station Korea."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv

from homeassistant import config_entries
from homeassistant.core import callback

from .const import DOMAIN, OIL_TYPE, OIL_TYPE_CODE, CONF_OIL_TYPE, CONF_STATION_ID, CONF_STATION_NAME, NATIONAL_AVR

_LOGGER = logging.getLogger(__name__)

class GasStationPriceConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gas Station Price."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow."""
        self._station_id: Required[str] = None
        self._oil_type: Required[str] = None
        self._station_name: Optional[str] = None

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            self._oil_type = user_input[CONF_OIL_TYPE]
            self._station_id = user_input[CONF_STATION_ID]

            if CONF_STATION_NAME in user_input:
                self._station_name = user_input[CONF_STATION_NAME]
            else:
                if self._station_id == "0":
                    self._station_name = NATIONAL_AVR
                else:
                    self._station_name = self._station_id

            key = f'oil-price-{self._station_id}-{ OIL_TYPE_CODE[self._oil_type]}'
            await self.async_set_unique_id(key)

            stitle = f'{self._station_name}-{OIL_TYPE[self._oil_type]}'

            _LOGGER.debug("key: %s, stitle: %s", key, stitle)

            return self.async_create_entry(title=stitle, data=user_input)

        #if self._async_current_entries():
        #    return self.async_abort(reason="single_instance_allowed")

        if user_input is None:
            return self._show_user_form(errors)

    async def async_step_import(self, import_info):
        """Handle import from config file."""
        return await self.async_step_user(import_info)

    @callback
    def _show_user_form(self, errors=None):
        schema = vol.Schema(
            {
                vol.Required(CONF_STATION_ID, default=None): str,
                vol.Required(CONF_OIL_TYPE, default='02'): vol.In(OIL_TYPE),
                vol.Optional(CONF_STATION_NAME): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors or {}
        )
