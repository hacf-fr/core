"""Config flow to configure the Sun integration."""
import logging
from typing import Any, Dict

from homeassistant import config_entries

from . import DOMAIN  # pylint: disable=unused-import

_LOGGER = logging.getLogger(__name__)


class SunFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_ASSUMED

    def _show_setup_form(self, user_input=None) -> Dict[str, Any]:
        """Show the setup form to the user."""
        return self.async_show_form(
            step_id="user",
        )

    async def async_step_user(self, user_input=None) -> Dict[str, Any]:
        """Handle a flow initiated by the user."""
        if user_input is None:
            return self._show_setup_form(user_input)

        # Check if already configured
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=DOMAIN,
            data={},
        )

    async def async_step_import(self, user_input=None) -> Dict[str, Any]:
        """Import a config entry."""
        return await self.async_step_user(user_input)
