"""The Enedis Linky integration."""
import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow, config_validation as cv

from . import api, config_flow
from .const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Required(CONF_CLIENT_SECRET): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["sensor"]


_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Enedis Linky component."""
    hass.data[DOMAIN] = {}

    _LOGGER.warning("async_setup")

    if DOMAIN not in config:
        return True

    _LOGGER.warning("DOMAIN in config")
    _LOGGER.warning(config[DOMAIN])

    config_flow.LinkyFlowHandler.async_register_implementation(
        hass,
        config_entry_oauth2_flow.LocalOAuth2Implementation(
            hass,
            DOMAIN,
            config[DOMAIN][CONF_CLIENT_ID],
            config[DOMAIN][CONF_CLIENT_SECRET],
            OAUTH2_AUTHORIZE,
            OAUTH2_TOKEN,
        ),
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Enedis Linky from a config entry."""
    _LOGGER.warning("async_setup_entry")
    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )
    _LOGGER.warning("async_setup_entry implementation")

    hass.data[DOMAIN][entry.entry_id] = api.ConfigEntryLinkyAuth(
        hass, entry, implementation
    )
    _LOGGER.warning("async_setup_entry ConfigEntryLinkyAuth")

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
