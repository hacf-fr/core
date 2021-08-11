"""Support for Freebox Delta, Revolution and Mini 4K."""
from __future__ import annotations

import logging

from freebox_api.exceptions import HttpRequestError, InsufficientPermissionsError

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .router import FreeboxRouter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the switch."""
    router = hass.data[DOMAIN][entry.unique_id]
    entities = [FreeboxWifiSwitch(router)]

    try:
        await router.connection.get_lte_config()
        entities.append(FreeboxLteSwitch(router))
    except HttpRequestError:
        _LOGGER.info("No 4G module detected")

    async_add_entities(entities, True)


class FreeboxWifiSwitch(SwitchEntity):
    """Representation of a freebox wifi switch."""

    def __init__(self, router: FreeboxRouter) -> None:
        """Initialize the Wifi switch."""
        self._name = "Freebox WiFi"
        self._icon = "mdi:wifi"
        self._state = None
        self._router = router
        self._unique_id = f"{self._router.mac} {self._name}"

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._state

    @property
    def icon(self) -> str:
        """Return the icon."""
        return self._icon

    def device_info(self) -> DeviceInfo:
        """Return the device information."""
        return self._router.device_info

    async def _async_set_state(self, enabled: bool):
        """Turn the switch on or off."""
        wifi_config = {"enabled": enabled}
        try:
            await self._router.wifi.set_global_config(wifi_config)
        except InsufficientPermissionsError:
            _LOGGER.warning(
                "Home Assistant does not have permissions to modify the Freebox settings. Please refer to documentation"
            )

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._async_set_state(False)

    async def async_update(self):
        """Get the state and update it."""
        datas = await self._router.wifi.get_global_config()
        active = datas["enabled"]
        self._state = bool(active)


class FreeboxLteSwitch(FreeboxWifiSwitch):
    """Representation of a freebox LTE switch."""

    def __init__(self, router: FreeboxRouter) -> None:
        """Initialize the LTE switch."""
        super().__init__(router)
        self._name = "Freebox LTE"
        self._icon = "mdi:signal-4g"
        self._unique_id = f"{self._router.mac} {self._name}"

    async def _async_set_state(self, enabled: bool):
        """Turn the switch on or off."""
        lte_config = {"enabled": enabled}
        try:
            await self._router.connection.set_lte_config(lte_config)
        except InsufficientPermissionsError:
            _LOGGER.warning(
                "Home Assistant does not have permissions to modify the Freebox LTE settings. Please refer to documentation"
            )

    async def async_update(self):
        """Get the state and update it."""
        datas = await self._router.connection.get_lte_config()
        active = datas["enabled"]
        self._state = bool(active)
