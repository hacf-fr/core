"""Support for Synology DSM sensors."""
from datetime import timedelta

from synology_dsm.api.download_station.task import SynoDownloadTask
from homeassistant.helpers.config_validation import time
from typing import Dict
import re

from synology_dsm.api.download_station import SynoDownloadStation

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DISKS,
    DATA_MEGABYTES,
    DATA_RATE_KILOBYTES_PER_SECOND,
    DATA_TERABYTES,
    PRECISION_TENTHS,
    TEMP_CELSIUS,
)
from homeassistant.helpers.temperature import display_temp
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers.event import async_call_later
from homeassistant.util.dt import utcnow
from homeassistant.util import Throttle

from . import (
    SynoApi,
    SynologyDSMDeviceEntity,
    SynologyDSMDispatcherEntity,
    SynologyDSMTaskEntity,
)
from .const import (
    CONF_VOLUMES,
    DOMAIN,
    DOWNLOAD_STATION_SENSORS,
    DOWNLOAD_STATION_TASK_SENSORS,
    ENTITY_UNIT_LOAD,
    INFORMATION_SENSORS,
    STORAGE_DISK_SENSORS,
    STORAGE_VOL_SENSORS,
    SYNO_API,
    TEMP_SENSORS_KEYS,
    UTILISATION_SENSORS,
    getDownloadTaskAttributes,
)


async def async_setup_entry(
    hass: HomeAssistantType, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Synology NAS Sensor."""

    api = hass.data[DOMAIN][entry.unique_id][SYNO_API]

    entities = [
        SynoDSMUtilSensor(api, sensor_type, UTILISATION_SENSORS[sensor_type])
        for sensor_type in UTILISATION_SENSORS
    ]

    # Handle all volumes
    if api.storage.volumes_ids:
        for volume in entry.data.get(CONF_VOLUMES, api.storage.volumes_ids):
            entities += [
                SynoDSMStorageSensor(
                    api, sensor_type, STORAGE_VOL_SENSORS[sensor_type], volume
                )
                for sensor_type in STORAGE_VOL_SENSORS
            ]

    # Handle all disks
    if api.storage.disks_ids:
        for disk in entry.data.get(CONF_DISKS, api.storage.disks_ids):
            entities += [
                SynoDSMStorageSensor(
                    api, sensor_type, STORAGE_DISK_SENSORS[sensor_type], disk
                )
                for sensor_type in STORAGE_DISK_SENSORS
            ]

    entities += [
        SynoDSMInfoSensor(api, sensor_type, INFORMATION_SENSORS[sensor_type])
        for sensor_type in INFORMATION_SENSORS
    ]

    if SynoDownloadStation.INFO_API_KEY in api.dsm.apis:
        await hass.async_add_executor_job(api.dsm.download_station.update)
        info = await hass.async_add_executor_job(api.dsm.download_station.get_info)
        version = info["data"]["version_string"]
        entities += [
            SynoDSMDownloadSensor(
                api, sensor_type, DOWNLOAD_STATION_SENSORS[sensor_type], version
            )
            for sensor_type in DOWNLOAD_STATION_SENSORS
        ]

    if SynoDownloadStation.TASK_API_KEY in api.dsm.apis:
        data = SynoDSMDownloadTaskData(
            hass,
            async_add_entities,
            api,
        )
        await data.async_update()

    async_add_entities(entities)


class SynoDSMUtilSensor(SynologyDSMDispatcherEntity):
    """Representation a Synology Utilisation sensor."""

    @property
    def state(self):
        """Return the state."""
        attr = getattr(self._api.utilisation, self.entity_type)
        if callable(attr):
            attr = attr()
        if attr is None:
            return None

        # Data (RAM)
        if self._unit == DATA_MEGABYTES:
            return round(attr / 1024.0 ** 2, 1)

        # Network
        if self._unit == DATA_RATE_KILOBYTES_PER_SECOND:
            return round(attr / 1024.0, 1)

        # CPU load average
        if self._unit == ENTITY_UNIT_LOAD:
            return round(attr / 100, 2)

        return attr

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._api.utilisation)


class SynoDSMStorageSensor(SynologyDSMDeviceEntity):
    """Representation a Synology Storage sensor."""

    @property
    def state(self):
        """Return the state."""
        attr = getattr(self._api.storage, self.entity_type)(self._device_id)
        if attr is None:
            return None

        # Data (disk space)
        if self._unit == DATA_TERABYTES:
            return round(attr / 1024.0 ** 4, 2)

        # Temperature
        if self.entity_type in TEMP_SENSORS_KEYS:
            return display_temp(self.hass, attr, TEMP_CELSIUS, PRECISION_TENTHS)

        return attr


class SynoDSMInfoSensor(SynologyDSMDispatcherEntity):
    """Representation a Synology information sensor."""

    def __init__(self, api: SynoApi, entity_type: str, entity_info: Dict[str, str]):
        """Initialize the Synology SynoDSMInfoSensor entity."""
        super().__init__(api, entity_type, entity_info)
        self._previous_uptime = None
        self._last_boot = None

    @property
    def state(self):
        """Return the state."""
        attr = getattr(self._api.information, self.entity_type)
        if attr is None:
            return None

        # Temperature
        if self.entity_type in TEMP_SENSORS_KEYS:
            return display_temp(self.hass, attr, TEMP_CELSIUS, PRECISION_TENTHS)

        if self.entity_type == "uptime":
            # reboot happened or entity creation
            if self._previous_uptime is None or self._previous_uptime > attr:
                last_boot = utcnow() - timedelta(seconds=attr)
                self._last_boot = last_boot.replace(microsecond=0).isoformat()

            self._previous_uptime = attr
            return self._last_boot
        return attr


class SynoDSMDownloadSensor(SynologyDSMDispatcherEntity):
    """Representation a Synology Download Station sensor."""

    def __init__(
        self, api: SynoApi, entity_type: str, entity_info: Dict[str, str], version: str
    ):
        """Initialize a Synology Download Station."""
        super().__init__(
            api,
            entity_type,
            entity_info,
        )
        self._version = version

    @property
    def state(self):
        """Return the state."""
        # attr = getattr(self._api.download_station, self.entity_type)
        # attr = await self.hass.async_add_executor_job(self._api.dsm.download_station.get_info)["data"][self.entity_type]
        attr = 0
        if attr is None:
            return None

        # DL/UP
        if self._unit == DATA_RATE_KILOBYTES_PER_SECOND:
            return round(attr / 1024.0, 1)

        return attr

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return bool(self._api.download_station)

    @property
    def device_info(self) -> Dict[str, any]:
        """Return the device information."""
        return {
            "identifiers": {
                (DOMAIN, self._api.information.serial, SynoDownloadStation.INFO_API_KEY)
            },
            "name": "Download Station",
            "manufacturer": "Synology",
            "model": self._api.information.model,
            "sw_version": self._version,
            "via_device": (DOMAIN, self._api.information.serial),
        }


class SynoDSMDownloadTaskData:
    """Define a data handler for SynoDSMDownloadTaskData."""

    def __init__(self, hass: HomeAssistantType, async_add_entities, api: SynoApi):
        """Initialize."""
        self._hass = hass
        self._async_add_entities = async_add_entities
        self._tasks = {}
        self._api = api
        self._reg = None

        self.async_update = Throttle(timedelta(seconds=15))(self._async_update)

    async def _cleanupUnavailable(self):
        if not self._reg:
            self._reg = await self._hass.helpers.entity_registry.async_get_registry()
        p = re.compile(
            f"sensor.{self._api.network.hostname.lower()}_.*_download"
        )  # TODO: pas générique
        states = self._hass.states.async_all("sensor")
        for entity in states:
            if p.match(entity.entity_id) and entity.state == "unavailable":
                try:
                    self._reg.async_remove(entity.entity_id)
                except KeyError:
                    continue

    async def _async_update(self):
        """Get updated data from Synology DownloadStation."""
        await self._cleanupUnavailable()

        await self._hass.async_add_executor_job(self._api.download_station.update)
        tasks = self._api.download_station.get_all_tasks()
        new_tasks = {t.id: t for t in tasks}
        to_add = set(new_tasks) - set(self._tasks)
        self._tasks = new_tasks
        entities = []
        if to_add:
            for task_id in to_add:
                entities += [
                    SynoDSMDownloadTaskSensor(
                        self._hass,
                        self._api,
                        self,
                        sensor_type,
                        DOWNLOAD_STATION_TASK_SENSORS[sensor_type],
                        task_id,
                    )
                    for sensor_type in DOWNLOAD_STATION_TASK_SENSORS
                ]

        self._async_add_entities(entities)


class SynoDSMDownloadTaskSensor(SynologyDSMTaskEntity):
    """Representation a Synology DownloadStation task sensor."""

    def __init__(
        self,
        hass: HomeAssistantType,
        api: SynoApi,
        data: SynoDSMDownloadTaskData,
        entity_type: str,
        entity_info: Dict[str, str],
        task_id: str,
    ):
        """Initialize the Synology SynoDSMInfoSensor entity."""
        super().__init__(api, entity_type, entity_info, task_id)
        self._hass = hass
        self._data = data
        self._task: SynoDownloadTask = self._data._tasks[self._task_id]
        self._attrs = getDownloadTaskAttributes(self._task)
        self._friendly_name = self._task.title

    @property
    def state(self):
        """Return the state."""
        return self._task.status

    @property
    def device_state_attributes(self):
        """Return other details about the sensor state."""
        return self._attrs

    async def async_update(self):
        """Update the sensor."""

        await self._data.async_update()

        if not self.available:
            async_call_later(self._hass, 1, self._remove)
            return

        if not self._task_id in self._data._tasks:
            async_call_later(self._hass, 1, self._remove)
            return

        self._state = self._task.status
        self._attrs = getDownloadTaskAttributes(self._task)

    async def _remove(self, *_):
        """Remove entity itself."""
        await self.async_remove()

        reg = await self.hass.helpers.entity_registry.async_get_registry()
        entity_id = reg.async_get_entity_id(
            "sensor",
            "{self._api.network.hostname}_",
            f"{self._task_id}_download",  # TODO: pas générique
        )
        if entity_id:
            reg.async_remove(entity_id)