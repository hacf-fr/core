"""Config flow for Enedis."""
import logging
from typing import Optional, cast
from aiohttp import web
from homeassistant.components.http.view import HomeAssistantView

from homeassistant import config_entries
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import get_url
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from urllib.parse import urlencode
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    CONF_USAGE_POINT_ID,
    DOMAIN,
    OAUTH2_AUTHORIZE,
    AUTH_CALLBACK_NAME,
    AUTH_CALLBACK_PATH,
    OAUTH2_TOKEN,
)

_LOGGER = logging.getLogger(__name__)


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """Config flow to handle Enedis OAuth2 authentication."""

    DOMAIN = DOMAIN
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize flow."""
        super().__init__()
        self._registered_view = False

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return logging.getLogger(__name__)

    # @property
    # def extra_authorize_data(self) -> dict:
    #     """Extra data that needs to be appended to the authorize url."""
    #     return {"flow_id": self.flow_id}

    def _generate_view(self):
        self.hass.http.register_view(EnedisAuthorizationCallbackView())
        self._registered_view = True

    # async def async_oauth_create_entry(self, data: dict) -> dict:
    #     pass

    async def async_step_user(self, user_input: Optional[dict] = None) -> dict:
        """Handle a flow start."""
        _LOGGER.error("async_step_user")
        _LOGGER.error(user_input)

        if self.hass.data.get(DOMAIN) and self.hass.data[DOMAIN].get(self.flow_id):
            _LOGGER.error("self.hass.data[DOMAIN][self.flow_id]")
            self.flow_impl = self.hass.data[DOMAIN][self.flow_id]

        if not self.flow_impl:
            _LOGGER.error("flow_impl")
            self.flow_impl = EnedisLocalOAuth2Implementation(self.hass, self.flow_id)
            self.hass.data.setdefault(DOMAIN, {})
            self.hass.data[DOMAIN][self.flow_id] = self.flow_impl

        if not self._registered_view:
            _LOGGER.error("_registered_view")
            self._generate_view()

        if not user_input:
            _LOGGER.error("async_step_auth")
            return await self.async_step_auth()

        _LOGGER.error("refresh_token")
        self.flow_impl.refresh_token = user_input[CONF_REFRESH_TOKEN]

        # Check if already configured
        await self.async_set_unique_id(user_input[CONF_USAGE_POINT_ID])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=user_input[CONF_USAGE_POINT_ID],
            data={
                CONF_REFRESH_TOKEN: user_input[CONF_REFRESH_TOKEN],
                CONF_ACCESS_TOKEN: user_input[CONF_ACCESS_TOKEN],
                CONF_USAGE_POINT_ID: user_input[CONF_USAGE_POINT_ID],
            },
        )

    async def async_oauth_create_entry(self, data: dict) -> dict:
        """Create an entry for the flow."""
        return self.async_create_entry(title=self.flow_impl.name, data=data)


class EnedisLocalOAuth2Implementation(
    config_entry_oauth2_flow.LocalOAuth2Implementation
):
    """Oauth2 implementation that only uses the external url."""

    def __init__(
        self, hass: HomeAssistant, flow_id: str,
    ):
        super().__init__(
            hass, DOMAIN, "None", "None", OAUTH2_AUTHORIZE, OAUTH2_TOKEN,
        )
        self.flow_id = flow_id
        self.refresh_token = None

    @property
    def redirect_uri(self) -> str:
        """Return the redirect uri."""
        url = get_url(self.hass, allow_internal=False, prefer_external=True)
        return f"{url}{AUTH_CALLBACK_PATH}"

    @property
    def extra_authorize_data(self) -> dict:
        """Extra data that needs to be appended to the authorize url."""
        return {"box": "HA", "flow_id": self.flow_id}

    async def _token_request(self, data: dict) -> dict:
        """Make a token request."""
        print("_token_request")
        session = async_get_clientsession(self.hass)

        params = {"grant_type": "refresh_token", "box_type": "Home-Assistant", "env": "prod"}
        params["refresh_token"] = self.refresh_token
        params["box_url"] = self.redirect_uri
        params["flow_id"] = self.flow_id

        print("_token_request params")
        print(params)
        print("_token_request data")
        print(data)

        print("--------------")
        print("URL_CONSTRUITE")
        print(f"{self.token_url}?{urlencode(params)}")
        print("--------------")
        print("STOP")

        return None

        resp = await session.post(self.token_url, params=params, data=data)
        resp.raise_for_status()
        print("_token_request url")
        print(resp.url)
        return cast(dict, await resp.json())


class EnedisAuthorizationCallbackView(HomeAssistantView):
    """Handle callback from external auth."""

    url = AUTH_CALLBACK_PATH
    name = AUTH_CALLBACK_NAME
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        """Receive authorization confirmation."""
        _LOGGER.warning("EnedisAuthorizationCallbackView")
        _LOGGER.warning(request.query)

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
        hass.data[DOMAIN][request.query["flow_id"]].refresh_token = request.query[
            "refresh_token"
        ]
        await hass.config_entries.flow.async_configure(
            flow_id=request.query["flow_id"], user_input=request.query
        )

        return web.Response(
            headers={"content-type": "text/html"},
            text="<script>window.close()</script>Success! This window can be closed",
        )
