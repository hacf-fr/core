"""The Enedis Linky integration."""
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

PLATFORMS = ["sensor"]


_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Enedis Linky component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Enedis Linky from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.warning("async_setup_entry")
    # implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
    #     hass, entry
    # )
    _LOGGER.warning("async_setup_entry implementation")

    # hass.data[DOMAIN][entry.entry_id] = api.ConfigEntryLinkyAuth(
    #     hass, entry, implementation
    # )
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
