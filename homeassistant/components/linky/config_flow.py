"""Config flow for Enedis Linky."""
import logging

from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class LinkyFlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Enedis Linky OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    # async def async_step_user(self, user_input=None):
    #     """Handle a flow start."""
    #     if self.hass.config_entries.async_entries(DOMAIN):
    #         return self.async_abort(reason="already_setup")

    #     return await super().async_step_user(user_input)
