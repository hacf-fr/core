"""Config flow for Enedis Linky."""
import logging
from typing import Optional
from urllib.parse import urlencode

from aiohttp import web

from homeassistant import config_entries
from homeassistant.components.http import HomeAssistantView
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.network import get_url

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AUTH_CALLBACK_PATH = "/auth/external/linky"


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

    async def async_step_user(self, user_input: Optional[dict] = None) -> dict:
        """Go to the auth step."""
        return await self.async_step_auth()

    async def async_step_auth(self, user_input: Optional[dict] = None) -> dict:
        """Create an entry for auth."""
        # Flow has been triggered by external data
        _LOGGER.error("starting_auth_config")
        if user_input:
            _LOGGER.error("getting_params_from_auth")
            self.external_data = user_input
            _LOGGER.error(self.external_data)
            return self.async_external_step_done(next_step_id="creation")

        params = urlencode(
            {
                "flow_id": self.flow_id,
                "redirect_uri": f"{get_url(self.hass)}{AUTH_CALLBACK_PATH}",
                "box": "HA",
            }
        )

        _LOGGER.error("openning_auth_url")
        return self.async_external_step(
            step_id="auth",
            url=f"http://www.sud-domotique-expert.fr/enedis/accord_enedis_prod.html?{params}",
        )


class LinkyAuthorizeCallbackView(HomeAssistantView):
    """Linky Authorization Callback View."""

    requires_auth = False
    url = AUTH_CALLBACK_PATH
    name = "auth:external:linky"

    async def get(self, request: web.Request) -> web.Response:
        """Receive authorization code."""
        if (
            "refresh_token" not in request.query
            or "access_token" not in request.query
            or "usage_point_id" not in request.query
            or "flow_id" not in request.query
        ):
            return web.Response(
                text=f"Missing refresh_token or access_token or usage_point_id or flow_id parameter in {request.url}"
            )

        hass = request.app["hass"]

        await hass.config_entries.flow.async_configure(
            flow_id=request.query["flow_id"], user_input=request.query
        )

        return web.Response(
            headers={"content-type": "text/html"},
            text="<script>window.close()</script>",
        )
