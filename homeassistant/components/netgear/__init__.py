"""Support for Netgear routers."""
import asyncio
from datetime import timedelta
import logging

from pynetgear import Netgear
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=30)

NETGEAR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_HOST): cv.string,
        vol.Optional(CONF_PORT): cv.port,
        vol.Optional(CONF_SSL, default=False): cv.boolean,
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [NETGEAR_SCHEMA]))},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up the Netgear component."""
    conf = config.get(DOMAIN)

    if conf is None:
        return True

    for netgear_conf in conf:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=netgear_conf,
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    """Set up Netgear component."""

    api = await hass.async_add_executor_job(
        Netgear,
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_HOST),
        entry.data.get(CONF_USERNAME),
        entry.data.get(CONF_PORT),
        entry.data.get(CONF_SSL),
    )
    await hass.async_add_executor_job(api.login)

    async def _async_update_data_device():
        """Fetch data from API endpoint."""
        return await hass.async_add_executor_job(api.get_attached_devices_2)

    coordinator_device = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"Netgear devices for {entry.title}",
        update_method=_async_update_data_device,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator_device.async_refresh()

    if not coordinator_device.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator_device

    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, platform)
        )

    return True


async def async_unload_entry(hass: HomeAssistantType, entry: ConfigEntry):
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
        await hass.data[DOMAIN][entry.unique_id].async_unload()
        hass.data[DOMAIN].pop(entry.unique_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok
