"""Support for Freebox covers."""
import base64
import json
import logging
import time

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DEVICE_CLASS_AWNING,
    DEVICE_CLASS_GARAGE,
    DEVICE_CLASS_SHUTTER,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_CLOSED, STATE_CLOSING, STATE_OPEN, STATE_OPENING
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .base_class import FreeboxHomeBaseClass
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    router = hass.data[DOMAIN][entry.unique_id]
    tracked = set()

    @callback
    def update_callback():
        add_entities(hass, router, async_add_entities, tracked)

    router.listeners.append(
        async_dispatcher_connect(hass, router.signal_home_device_new, update_callback)
    )
    update_callback()


@callback
def add_entities(hass, router, async_add_entities, tracked):
    """Add new Alarm Control Panel from the router."""
    new_tracked = []

    for nodeId, node in router.home_devices.items():
        if nodeId in tracked:
            continue
        if node["category"] == "basic_shutter":
            new_tracked.append(FreeboxBasicShutter(hass, router, node))
            tracked.add(nodeId)
        elif node["category"] == "shutter" or node["category"] == "opener":
            new_tracked.append(FreeboxShutter(hass, router, node))
            tracked.add(nodeId)
        elif node["category"] == "opener":
            new_tracked.append(FreeboxOpener(hass, router, node))
            tracked.add(nodeId)

    if new_tracked:
        async_add_entities(new_tracked, True)


class FreeboxBasicShutter(FreeboxHomeBaseClass, CoverEntity):
    def __init__(self, hass, router, node) -> None:
        """Initialize a Cover"""
        super().__init__(hass, router, node)
        self._command_up = self.get_command_id(node["show_endpoints"], "slot", "up")
        self._command_stop = self.get_command_id(node["show_endpoints"], "slot", "stop")
        self._command_down = self.get_command_id(node["show_endpoints"], "slot", "down")
        self._command_state = self.get_command_id(
            node["show_endpoints"], "signal", "state"
        )
        self._state = self.convert_state(self.get_value("signal", "state"))

    @property
    def device_class(self) -> str:
        return DEVICE_CLASS_SHUTTER

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        if self._state == STATE_OPEN:
            return False
        if self._state == STATE_CLOSED:
            return True
        return None

    async def async_open_cover(self, **kwargs):
        """Open cover."""
        await self.set_home_endpoint_value(self._command_up, {"value": None})
        await self.async_set_value("signal", "state", False)

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        await self.set_home_endpoint_value(self._command_down, {"value": None})
        await self.async_set_value("signal", "state", True)

    async def async_stop_cover(self, **kwargs):
        """Stop cover."""
        await self.set_home_endpoint_value(self._command_stop, {"value": None})
        await self.async_set_value("signal", "state", None)

    async def async_update_node(self):
        """Update state"""
        self._state = self.convert_state(self.get_value("signal", "state"))

    def convert_state(self, state):
        if state:
            return STATE_CLOSED
        elif state is not None:
            return STATE_OPEN
        else:
            return None


class FreeboxShutter(FreeboxHomeBaseClass, CoverEntity):
    def __init__(self, hass, router, node) -> None:
        """Initialize a Cover"""
        # For the dev I got
        # DEVICE_CLASS_SHUTTER  = RTS
        # DEVICE_CLASS_GARAGE   = IOHome
        super().__init__(hass, router, node)
        self._command_set_position = self.get_command_id(
            node["show_endpoints"], "slot", "position_set"
        )
        self._command_stop = self.get_command_id(node["show_endpoints"], "slot", "stop")
        self._command_position = self.get_command_id(
            node["type"]["endpoints"], "slot", "position"
        )
        self._device_class = DEVICE_CLASS_SHUTTER
        self._supported_features = (
            SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_SET_POSITION | SUPPORT_STOP
        )
        self._invert_position = True

        if node["category"] == "opener":
            self._device_class = DEVICE_CLASS_AWNING

            if "Porte_Garage" in node["type"]["icon"]:  # Dexxo Smart IO
                self._invert_position = False
                self._device_class = DEVICE_CLASS_GARAGE
                # self._supported_features  = SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP

        self.update_current_position()

    @property
    def device_class(self) -> str:
        return self._device_class

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features

    @property
    def current_cover_position(self):
        """Return current position of cover.
        None is unknown, 0 is closed, 100 is fully open.
        """
        return self._current_position

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        return self.current_cover_position == 0

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        value = (
            100 - kwargs[ATTR_POSITION]
            if (self._invert_position)
            else kwargs[ATTR_POSITION]
        )
        await self.set_home_endpoint_value(self._command_set_position, {"value": value})
        self._current_position = kwargs[ATTR_POSITION]
        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs):
        """Open cover."""
        value = 0 if (self._invert_position) else 100
        await self.set_home_endpoint_value(self._command_set_position, {"value": value})
        self._current_position = 100
        self.async_write_ha_state()

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        value = 100 if (self._invert_position) else 0
        await self.set_home_endpoint_value(self._command_set_position, {"value": value})
        self._current_position = 0
        self.async_write_ha_state()

    async def async_stop_cover(self, **kwargs):
        """Stop cover."""
        await self.set_home_endpoint_value(self._command_stop, {"value": None})
        self.update_current_position()
        self.async_write_ha_state()

    def update_current_position(self):
        """ Set the current position """
        # Parse current status
        state = self.get_value("signal", "state")
        position_set = self.get_value("signal", "position_set")

        hex_value = base64.b64decode(state).hex()
        if len(hex_value) != 118:
            _LOGGER.warning("Invalid state: " + str(state))
            # Use basic method to set position
            self._current_position = (
                (100 - position_set) if self._invert_position else position_set
            )
            return

        # Get the two important values
        val_1 = hex_value[96:98]
        val_2 = hex_value[100:102]

        # Open
        if val_2 == "00":
            self._current_position = 100
        # Close
        elif val_2 == "c8":
            self._current_position = 0
        else:
            # Check if the position current value can be used
            if position_set > 0 and position_set < 100:
                self._current_position = (
                    (100 - position_set) if self._invert_position else position_set
                )
            else:  # set 50% (because why not!)
                self._current_position = 50

        # Dump
        _LOGGER.debug(
            "Details ["
            + str(position_set)
            + "/"
            + val_1
            + "/"
            + val_2
            + "] with state: "
            + str(state)
        )

    async def async_update_node(self):
        self.update_current_position()
