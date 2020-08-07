"""API for Enedis bound to Home Assistant OAuth."""
from asyncio import run_coroutine_threadsafe
import logging

from aiohttp import ClientSession
import enedis

from homeassistant import config_entries, core
from homeassistant.helpers import config_entry_oauth2_flow

_LOGGER = logging.getLogger(__name__)


class ConfigEntryAuth(enedis.AbstractAuth):
    """Provide Enedis authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation,
    ):
        """Initialize Enedis Auth."""
        self.hass = hass
        self.config_entry = config_entry
        self.session = config_entry_oauth2_flow.OAuth2Session(
            hass, config_entry, implementation
        )
        _LOGGER.debug("ConfigEntryAuth.init")
        _LOGGER.debug(self)
        _LOGGER.debug(super())
        super().__init__(self.session.token)

    def refresh_tokens(self) -> dict:
        """Refresh and return new Enedis tokens using Home Assistant OAuth2 session."""
        _LOGGER.debug("ConfigEntryAuth.refresh_tokens")
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.hass.loop
        ).result()
        _LOGGER.debug(self.session.token)

        return self.session.token
