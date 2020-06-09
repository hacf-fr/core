"""Config flow for Enedis Linky."""
import logging
from typing import Optional

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

    async def async_step_auth(self, user_input: Optional[dict] = None) -> dict:
        """Create an entry for auth."""
        # Flow has been triggered by external data
        if user_input:
            self.external_data = user_input
            return self.async_external_step_done(next_step_id="creation")

        return self.async_external_step(
            step_id="auth",
            url="http://www.sud-domotique-expert.fr/enedis/accord_enedis_prod.html",
        )
