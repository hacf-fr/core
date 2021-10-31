"""Support for Meteo-France weather data."""
from datetime import timedelta
import logging
from typing import Any, Dict

from meteofrance_api.client import MeteoFranceClient
from meteofrance_api.helpers import is_valid_warning_department
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_CITY,
    COORDINATOR_ALERT,
    COORDINATOR_FORECAST,
    COORDINATOR_RAIN,
    DOMAIN,
    PLATFORMS,
    UNDO_UPDATE_LISTENER,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_RAIN = timedelta(minutes=5)
SCAN_INTERVAL = timedelta(minutes=15)


CITY_SCHEMA = vol.Schema({vol.Required(CONF_CITY): cv.string})

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {DOMAIN: vol.Schema(vol.All(cv.ensure_list, [CITY_SCHEMA]))},
    ),
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Meteo-France from legacy config file."""
    if not (conf := config.get(DOMAIN)):
        return True

    for city_conf in conf:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=city_conf
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an Meteo-France account from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = MeteoFranceClient()
    latitude = entry.data[CONF_LATITUDE]
    longitude = entry.data[CONF_LONGITUDE]

    async def _async_update_data_alert():
        """Fetch data from API endpoint."""
        return await hass.async_add_executor_job(
            client.get_warning_current_phenomenoms, department, 0, True
        )

    coordinator_forecast = MeteoFranceDataUpdateCoordinator(
        hass, client, "Lyon", "69000", latitude, longitude
    )
    coordinator_rain = None
    coordinator_alert = None

    # Fetch initial data so we have data when entities subscribe
    await coordinator_forecast.async_refresh()

    if not coordinator_forecast.last_update_success:
        raise ConfigEntryNotReady

    # Check if rain forecast is available.
    if coordinator_forecast.data.position.get("rain_product_available") == 1:
        coordinator_rain = MeteoFranceRainDataUpdateCoordinator(
            hass, client, "Lyon", "69000", latitude, longitude
        )
        await coordinator_rain.async_refresh()

        if not coordinator_rain.last_update_success:
            raise ConfigEntryNotReady
    else:
        _LOGGER.warning(
            "1 hour rain forecast not available. %s is not in covered zone",
            entry.title,
        )

    department = coordinator_forecast.data.position.get("dept")
    _LOGGER.debug(
        "Department corresponding to %s is %s",
        entry.title,
        department,
    )
    if is_valid_warning_department(department):
        if not hass.data[DOMAIN].get(department):
            coordinator_alert = DataUpdateCoordinator(
                hass,
                _LOGGER,
                name=f"Météo-France alert for department {department}",
                update_method=_async_update_data_alert,
                update_interval=SCAN_INTERVAL,
            )

            await coordinator_alert.async_refresh()

            if not coordinator_alert.last_update_success:
                raise ConfigEntryNotReady

            hass.data[DOMAIN][department] = True
        else:
            _LOGGER.warning(
                "Weather alert for department %s won't be added with city %s, as it has already been added within another city",
                department,
                entry.title,
            )
    else:
        _LOGGER.warning(
            "Weather alert not available: The city %s is not in metropolitan France or Andorre",
            entry.title,
        )

    undo_listener = entry.add_update_listener(_async_update_listener)

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR_FORECAST: coordinator_forecast,
        COORDINATOR_RAIN: coordinator_rain,
        COORDINATOR_ALERT: coordinator_alert,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if hass.data[DOMAIN][entry.entry_id][COORDINATOR_ALERT]:

        department = hass.data[DOMAIN][entry.entry_id][
            COORDINATOR_FORECAST
        ].data.position.get("dept")
        hass.data[DOMAIN][department] = False
        _LOGGER.debug(
            "Weather alert for depatment %s unloaded and released. It can be added now by another city",
            department,
        )

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class MeteoFranceDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching AccuWeather data API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MeteoFranceClient,
        city_name: str,
        city_zip: str,
        latitude: float,
        longitude: float,
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.client = client
        self.city_name = city_name
        self.city_zip = city_zip
        self.latitude = latitude
        self.longitude = longitude

        super().__init__(
            hass,
            _LOGGER,
            name=f"Météo-France forecast for city {city_name}",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        return await self.hass.async_add_executor_job(
            self.client.get_forecast, self.latitude, self.longitude
        )


class MeteoFranceRainDataUpdateCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Class to manage fetching AccuWeather data API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MeteoFranceClient,
        city_name: str,
        city_zip: str,
        latitude: float,
        longitude: float,
    ) -> None:
        """Initialize."""
        self.hass = hass
        self.client = client
        self.city_name = city_name
        self.city_zip = city_zip
        self.latitude = latitude
        self.longitude = longitude

        super().__init__(
            hass,
            _LOGGER,
            name=f"Météo-France rain for city {city_name}",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        return await self.hass.async_add_executor_job(
            self.client.get_rain, self.latitude, self.longitude
        )
