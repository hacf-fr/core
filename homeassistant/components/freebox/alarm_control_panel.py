"""Support for Freebox alarms."""
from datetime import datetime, timedelta
import logging
from typing import Dict, Optional

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_NIGHT,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_NIGHT,
    STATE_ALARM_ARMING,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .base_class import FreeboxHomeBaseClass
from .const import DOMAIN
from .router import FreeboxRouter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities) -> None:
    """Set up alarms."""
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
    """Add new alarms from the router."""
    new_tracked = []

    for nodeId, node in router.home_devices.items():
        if (node["category"] != "alarm") or (nodeId in tracked):
            continue
        new_tracked.append(FreeboxAlarm(hass, router, node))
        tracked.add(nodeId)

    if new_tracked:
        async_add_entities(new_tracked, True)


class FreeboxAlarm(FreeboxHomeBaseClass, AlarmControlPanelEntity):
    """Representation of a Freebox alarm."""

    def __init__(self, hass, router: FreeboxRouter, node: Dict[str, any]) -> None:
        """Initialize an alarm."""
        super().__init__(hass, router, node)

        # Trigger
        self._command_trigger = self.get_command_id(
            node["type"]["endpoints"], "slot", "trigger"
        )
        # Alarme principale
        self._command_alarm1 = self.get_command_id(
            node["type"]["endpoints"], "slot", "alarm1"
        )
        # Alarme secondaire
        self._command_alarm2 = self.get_command_id(
            node["type"]["endpoints"], "slot", "alarm2"
        )
        # Passer le délai
        self._command_skip = self.get_command_id(
            node["type"]["endpoints"], "slot", "skip"
        )
        # Désactiver l'alarme
        self._command_off = self.get_command_id(
            node["type"]["endpoints"], "slot", "off"
        )
        # Code PIN
        self._command_pin = self.get_command_id(
            node["type"]["endpoints"], "slot", "pin"
        )
        # Puissance des bips
        self._command_sound = self.get_command_id(
            node["type"]["endpoints"], "slot", "sound"
        )
        # Puissance de la sirène
        self._command_volume = self.get_command_id(
            node["type"]["endpoints"], "slot", "volume"
        )
        # Délai avant armement
        self._command_timeout1 = self.get_command_id(
            node["type"]["endpoints"], "slot", "timeout1"
        )
        # Délai avant sirène
        self._command_timeout2 = self.get_command_id(
            node["type"]["endpoints"], "slot", "timeout2"
        )
        # Durée de la sirène
        self._command_timeout3 = self.get_command_id(
            node["type"]["endpoints"], "slot", "timeout3"
        )
        # État
        self._command_state = self.get_command_id(
            node["type"]["endpoints"], "signal", "state"
        )

        self.set_state("idle")
        self._timeout1 = 15
        self._supported_features = SUPPORT_ALARM_ARM_AWAY
        self.update_node()

    @property
    def state(self) -> str:
        """Return the state."""
        return self._state

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return self._supported_features

    async def async_alarm_disarm(self, code=None) -> None:
        """Send disarm command."""
        if await self.set_home_endpoint_value(self._command_off):
            self._state = STATE_ALARM_DISARMED
            self.start_watcher(timedelta(seconds=1))
            self.async_write_ha_state()

    async def async_alarm_arm_away(self, code=None) -> None:
        """Send arm away command."""
        if await self.set_home_endpoint_value(self._command_alarm1):
            self._state = STATE_ALARM_ARMING
            self.start_watcher(timedelta(seconds=self._timeout1 + 1))
            self.async_write_ha_state()

    async def async_alarm_arm_night(self, code=None) -> None:
        """Send arm night command."""
        if await self.set_home_endpoint_value(self._command_alarm2):
            self._state = STATE_ALARM_ARMING
            self.start_watcher(timedelta(seconds=self._timeout1 + 1))
            self.async_write_ha_state()

    async def async_watcher(self, now: Optional[datetime] = None) -> None:
        """Get the state and update it."""
        self.set_state(await self.get_home_endpoint_value(self._command_state))
        self.async_write_ha_state()
        self.stop_watcher()

    async def async_update_node(self):
        """Get the state & name and update it."""
        self.set_state(await self.get_home_endpoint_value(self._command_state))
        self.update_node()

    def update_node(self):
        """Update the alarm."""
        # Search if Alarm2
        has_alarm2 = False
        for nodeId, local_node in self._router.home_devices.items():
            alarm2 = next(
                filter(
                    lambda x: (x["name"] == "alarm2" and x["ep_type"] == "signal"),
                    local_node["show_endpoints"],
                ),
                None,
            )
            if alarm2:
                has_alarm2 = alarm2["value"]
                break

        if has_alarm2:
            self._supported_features = SUPPORT_ALARM_ARM_AWAY | SUPPORT_ALARM_ARM_NIGHT
        else:
            self._supported_features = SUPPORT_ALARM_ARM_AWAY

        # Parse all endpoints values
        for endpoint in filter(
            lambda x: (x["ep_type"] == "signal"), self._node["show_endpoints"]
        ):
            if endpoint["name"] == "pin":
                self._pin = endpoint["value"]
            elif endpoint["name"] == "sound":
                self._sound = endpoint["value"]
            elif endpoint["name"] == "volume":
                self._high_volume = endpoint["value"]
            elif endpoint["name"] == "timeout1":
                self._timeout1 = endpoint["value"]
            elif endpoint["name"] == "timeout3":
                self._timeout2 = endpoint["value"]
            elif endpoint["name"] == "timeout3":
                self._timeout3 = endpoint["value"]
            elif endpoint["name"] == "battery":
                self._battery = endpoint["value"]

    def set_state(self, state: str):
        """Update state."""
        if state == "alarm1_arming":
            self._state = STATE_ALARM_ARMING
        elif state == "alarm2_arming":
            self._state = STATE_ALARM_ARMING
        elif state == "alarm1_armed":
            self._state = STATE_ALARM_ARMED_AWAY
        elif state == "alarm2_armed":
            self._state = STATE_ALARM_ARMED_NIGHT
        elif state == "alarm1_alert_timer":
            self._state = STATE_ALARM_TRIGGERED
        elif state == "alarm2_alert_timer":
            self._state = STATE_ALARM_TRIGGERED
        elif state == "alert":
            self._state = STATE_ALARM_TRIGGERED
        else:
            self._state = STATE_ALARM_DISARMED
