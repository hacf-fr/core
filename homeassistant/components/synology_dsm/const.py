"""Constants for Synology DSM."""

import math
from synology_dsm.api.core.security import SynoCoreSecurity
from synology_dsm.api.core.upgrade import SynoCoreUpgrade
from synology_dsm.api.core.utilization import SynoCoreUtilization
from synology_dsm.api.download_station import SynoDownloadStation, SynoDownloadTask
from synology_dsm.api.dsm.information import SynoDSMInformation
from synology_dsm.api.storage.storage import SynoStorage
from synology_dsm.api.surveillance_station import SynoSurveillanceStation

from homeassistant.components.binary_sensor import DEVICE_CLASS_SAFETY
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    DATA_MEGABYTES,
    DATA_RATE_KILOBYTES_PER_SECOND,
    DATA_TERABYTES,
    DEVICE_CLASS_TEMPERATURE,
    DEVICE_CLASS_TIMESTAMP,
    PERCENTAGE,
)

ATTRIBUTION = "Data provided by Synology"

DOMAIN = "synology_dsm"
PLATFORMS = ["binary_sensor", "camera", "sensor", "switch"]
COORDINATOR_SURVEILLANCE = "coordinator_surveillance_station"

# Entry keys
SYNO_API = "syno_api"
UNDO_UPDATE_LISTENER = "undo_update_listener"

# Configuration
CONF_SERIAL = "serial"
CONF_VOLUMES = "volumes"

DEFAULT_USE_SSL = True
DEFAULT_VERIFY_SSL = False
DEFAULT_PORT = 5000
DEFAULT_PORT_SSL = 5001
# Options
DEFAULT_SCAN_INTERVAL = 15  # min
DEFAULT_TIMEOUT = 10  # sec

ENTITY_UNIT_LOAD = "load"

ENTITY_NAME = "name"
ENTITY_UNIT = "unit"
ENTITY_ICON = "icon"
ENTITY_CLASS = "device_class"
ENTITY_ENABLE = "enable"

# Services
SERVICE_REBOOT = "reboot"
SERVICE_SHUTDOWN = "shutdown"
SERVICE_TASK = "task_"
SERVICE_TASK_PAUSE = "task_pause"
SERVICE_TASK_PAUSE_ALL = "task_pause_all"
SERVICE_TASK_RESUME = "task_resume"
SERVICE_TASK_RESUME_ALL = "task_resume_all"
SERVICE_TASK_DELETE = "task_delete"
SERVICE_TASK_DELETE_ALL = "task_delete_all"
SERVICE_TASK_CREATE = "task_create"
SERVICES = [
    SERVICE_REBOOT,
    SERVICE_SHUTDOWN,
    SERVICE_TASK_PAUSE,
    SERVICE_TASK_PAUSE_ALL,
    SERVICE_TASK_RESUME,
    SERVICE_TASK_RESUME_ALL,
    SERVICE_TASK_DELETE,
    SERVICE_TASK_DELETE_ALL,
    SERVICE_TASK_CREATE,
]
TASK_STATUSES = ["error", "finished", "downloading", "paused", "waiting"]
TASK_ID = "task_id"
TASK_ALL = "all"
TASK_FORCE_COMPLETE = "force_complete"
TASK_URI = "uri"
TASK_UNZIP_PASSWORD = "unzip_password"
TASK_DESTINATION = "destination"

TASK_ATTR_TITLE = "title"
TASK_ATTR_SIZE_VALUE = "size_value"
TASK_ATTR_SIZE = "size"
TASK_ATTR_STATUS = "status"
TASK_ATTR_CREATE_TIME = "create_time"
TASK_ATTR_DEST = "destination"
TASK_ATTR_STARTED_TIME = "started_time"
TASK_ATTR_SIZE_DOWNLOADED_VALUE = "size_downloaded_value"
TASK_ATTR_SIZE_UPLOADED_VALUE = "size_uploaded_value"
TASK_ATTR_SIZE_DOWNLOADED = "size_downloaded"
TASK_ATTR_SIZE_UPLOADED = "size_uploaded"
TASK_ATTR_SPEED_DOWNLOAD_VALUE = "speed_download_value"
TASK_ATTR_SPEED_UPLOAD_VALUE = "speed_upload_value"
TASK_ATTR_SPEED_DOWNLOAD = "speed_download"
TASK_ATTR_SPEED_UPLOAD = "speed_upload"
TASK_ATTR_SIZE_PERCENT = "downloaded_percent"

# Entity keys should start with the API_KEY to fetch

# Binary sensors
UPGRADE_BINARY_SENSORS = {
    f"{SynoCoreUpgrade.API_KEY}:update_available": {
        ENTITY_NAME: "Update available",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:update",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
}

SECURITY_BINARY_SENSORS = {
    f"{SynoCoreSecurity.API_KEY}:status": {
        ENTITY_NAME: "Security status",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_SAFETY,
        ENTITY_ENABLE: True,
    },
}

STORAGE_DISK_BINARY_SENSORS = {
    f"{SynoStorage.API_KEY}:disk_exceed_bad_sector_thr": {
        ENTITY_NAME: "Exceeded Max Bad Sectors",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_SAFETY,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:disk_below_remain_life_thr": {
        ENTITY_NAME: "Below Min Remaining Life",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_SAFETY,
        ENTITY_ENABLE: True,
    },
}

# Sensors
UTILISATION_SENSORS = {
    f"{SynoCoreUtilization.API_KEY}:cpu_other_load": {
        ENTITY_NAME: "CPU Utilization (Other)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_user_load": {
        ENTITY_NAME: "CPU Utilization (User)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_system_load": {
        ENTITY_NAME: "CPU Utilization (System)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_total_load": {
        ENTITY_NAME: "CPU Utilization (Total)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_1min_load": {
        ENTITY_NAME: "CPU Load Averarge (1 min)",
        ENTITY_UNIT: ENTITY_UNIT_LOAD,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_5min_load": {
        ENTITY_NAME: "CPU Load Averarge (5 min)",
        ENTITY_UNIT: ENTITY_UNIT_LOAD,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:cpu_15min_load": {
        ENTITY_NAME: "CPU Load Averarge (15 min)",
        ENTITY_UNIT: ENTITY_UNIT_LOAD,
        ENTITY_ICON: "mdi:chip",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_real_usage": {
        ENTITY_NAME: "Memory Usage (Real)",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_size": {
        ENTITY_NAME: "Memory Size",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_cached": {
        ENTITY_NAME: "Memory Cached",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_available_swap": {
        ENTITY_NAME: "Memory Available (Swap)",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_available_real": {
        ENTITY_NAME: "Memory Available (Real)",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_total_swap": {
        ENTITY_NAME: "Memory Total (Swap)",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:memory_total_real": {
        ENTITY_NAME: "Memory Total (Real)",
        ENTITY_UNIT: DATA_MEGABYTES,
        ENTITY_ICON: "mdi:memory",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:network_up": {
        ENTITY_NAME: "Network Up",
        ENTITY_UNIT: DATA_RATE_KILOBYTES_PER_SECOND,
        ENTITY_ICON: "mdi:upload",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoCoreUtilization.API_KEY}:network_down": {
        ENTITY_NAME: "Network Down",
        ENTITY_UNIT: DATA_RATE_KILOBYTES_PER_SECOND,
        ENTITY_ICON: "mdi:download",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
}
STORAGE_VOL_SENSORS = {
    f"{SynoStorage.API_KEY}:volume_status": {
        ENTITY_NAME: "Status",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:checkbox-marked-circle-outline",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:volume_size_total": {
        ENTITY_NAME: "Total Size",
        ENTITY_UNIT: DATA_TERABYTES,
        ENTITY_ICON: "mdi:chart-pie",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoStorage.API_KEY}:volume_size_used": {
        ENTITY_NAME: "Used Space",
        ENTITY_UNIT: DATA_TERABYTES,
        ENTITY_ICON: "mdi:chart-pie",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:volume_percentage_used": {
        ENTITY_NAME: "Volume Used",
        ENTITY_UNIT: PERCENTAGE,
        ENTITY_ICON: "mdi:chart-pie",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:volume_disk_temp_avg": {
        ENTITY_NAME: "Average Disk Temp",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TEMPERATURE,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:volume_disk_temp_max": {
        ENTITY_NAME: "Maximum Disk Temp",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TEMPERATURE,
        ENTITY_ENABLE: False,
    },
}
STORAGE_DISK_SENSORS = {
    f"{SynoStorage.API_KEY}:disk_smart_status": {
        ENTITY_NAME: "Status (Smart)",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:checkbox-marked-circle-outline",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: False,
    },
    f"{SynoStorage.API_KEY}:disk_status": {
        ENTITY_NAME: "Status",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:checkbox-marked-circle-outline",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoStorage.API_KEY}:disk_temp": {
        ENTITY_NAME: "Temperature",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TEMPERATURE,
        ENTITY_ENABLE: True,
    },
}

INFORMATION_SENSORS = {
    f"{SynoDSMInformation.API_KEY}:temperature": {
        ENTITY_NAME: "temperature",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TEMPERATURE,
        ENTITY_ENABLE: True,
    },
    f"{SynoDSMInformation.API_KEY}:uptime": {
        ENTITY_NAME: "last boot",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: DEVICE_CLASS_TIMESTAMP,
        ENTITY_ENABLE: False,
    },
}

DOWNLOAD_STATION_SENSORS = {
    f"{SynoDownloadStation.STAT_API_KEY}:speed_download": {
        ENTITY_NAME: "speed download",
        ENTITY_UNIT: DATA_RATE_KILOBYTES_PER_SECOND,
        ENTITY_ICON: "mdi:download",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoDownloadStation.STAT_API_KEY}:speed_upload": {
        ENTITY_NAME: "speed upload",
        ENTITY_UNIT: DATA_RATE_KILOBYTES_PER_SECOND,
        ENTITY_ICON: "mdi:upload",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    # f"{SynoDownloadStation.TASK_API_KEY}:active_downloads": {
    #     ENTITY_NAME: "active downloads",
    #     ENTITY_UNIT: None,
    #     ENTITY_ICON: None,
    #     ENTITY_CLASS: None,
    #     ENTITY_ENABLE: True,
    # },
    f"{SynoDownloadStation.TASK_API_KEY}:paused_downloads": {
        ENTITY_NAME: "paused download",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoDownloadStation.TASK_API_KEY}:started_downloads": {
        ENTITY_NAME: "started downloads",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
    f"{SynoDownloadStation.TASK_API_KEY}:completed_downloads": {
        ENTITY_NAME: "completed downloads",
        ENTITY_UNIT: None,
        ENTITY_ICON: None,
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
}

DOWNLOAD_STATION_TASK_SENSORS = {
    f"{SynoDownloadStation.API_KEY}:download": {
        ENTITY_NAME: "Download",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:download",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
}

# Switch
SURVEILLANCE_SWITCH = {
    f"{SynoSurveillanceStation.HOME_MODE_API_KEY}:home_mode": {
        ENTITY_NAME: "home mode",
        ENTITY_UNIT: None,
        ENTITY_ICON: "mdi:home-account",
        ENTITY_CLASS: None,
        ENTITY_ENABLE: True,
    },
}


TEMP_SENSORS_KEYS = [
    "volume_disk_temp_avg",
    "volume_disk_temp_max",
    "disk_temp",
    "temperature",
]


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def convert_speed(size_bytes):
    return convert_size(size_bytes) + "/s"


def getDownloadTaskAttributes(task: SynoDownloadTask):
    return {
        ATTR_ATTRIBUTION: ATTRIBUTION,
        TASK_ATTR_TITLE: task.title,
        TASK_ATTR_SIZE_VALUE: task.size,
        TASK_ATTR_SIZE: convert_size(task.size),
        TASK_ATTR_STATUS: task.status,
        TASK_ATTR_CREATE_TIME: task.additional["detail"]["create_time"] * 1000,
        TASK_ATTR_DEST: task.additional["detail"]["destination"],
        TASK_ATTR_STARTED_TIME: task.additional["detail"]["started_time"] * 1000,
        TASK_ATTR_SIZE_DOWNLOADED_VALUE: task.additional["transfer"]["size_downloaded"],
        TASK_ATTR_SIZE_UPLOADED_VALUE: task.additional["transfer"]["size_uploaded"],
        TASK_ATTR_SIZE_DOWNLOADED: convert_size(
            task.additional["transfer"]["size_downloaded"]
        ),
        TASK_ATTR_SIZE_UPLOADED: convert_size(
            task.additional["transfer"]["size_uploaded"]
        ),
        TASK_ATTR_SPEED_DOWNLOAD_VALUE: task.additional["transfer"]["speed_download"],
        TASK_ATTR_SPEED_UPLOAD_VALUE: task.additional["transfer"]["speed_upload"],
        TASK_ATTR_SPEED_DOWNLOAD: convert_speed(
            task.additional["transfer"]["speed_download"]
        ),
        TASK_ATTR_SPEED_UPLOAD: convert_speed(
            task.additional["transfer"]["speed_upload"]
        ),
        TASK_ATTR_SIZE_PERCENT: round(
            (task.additional["transfer"]["size_downloaded"] / task.size) * 100
        )
        if task.size > 0
        else 0,
    }