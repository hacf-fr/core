"""Tests for the Meteo-France config flow."""
from meteofrance.exceptions import MeteoFranceException
from meteofrance.model import Place
import pytest

from homeassistant import data_entry_flow
from homeassistant.components.meteo_france.const import CONF_CITY, DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, SOURCE_USER
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE

from tests.async_mock import patch
from tests.common import MockConfigEntry

CITY_1_POSTAL = "74220"
CITY_1_NAME = "La Clusaz"
CITY_1_LAT = 45.90417
CITY_1_LON = 6.42306
CITY_1_COUNTRY = "FR"
CITY_1_ADMIN = "Rhône-Alpes"
CITY_1_ADMIN2 = "74"

CITY_2_POSTAL_DISTRICT_1 = "69001"
CITY_2_POSTAL_DISTRICT_4 = "69004"
CITY_2_NAME = "Lyon"


@pytest.fixture(name="client_1")
def mock_controller_client_1():
    """Mock a successful client."""
    with patch(
        "homeassistant.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        city_1 = Place(
            {
                "name": CITY_1_NAME,
                "lat": CITY_1_LAT,
                "lon": CITY_1_LON,
                "country": CITY_1_COUNTRY,
                "admin": CITY_1_ADMIN,
                "admin2": CITY_1_ADMIN2,
            }
        )
        service_mock.return_value.search_places.return_value = [city_1]
        yield service_mock


@pytest.fixture(autouse=True)
def mock_setup():
    """Prevent setup."""
    with patch(
        "homeassistant.components.meteo_france.async_setup", return_value=True,
    ), patch(
        "homeassistant.components.meteo_france.async_setup_entry", return_value=True,
    ):
        yield


@pytest.fixture(name="client_2")
def mock_controller_client_2():
    """Mock a successful client."""
    with patch(
        "homeassistant.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.get_data.return_value = {"name": CITY_2_NAME}
        yield service_mock


async def test_user(hass, client_1):
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["step_id"] == "user"

    # test with all provided with search returning only 1 place
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_CITY: CITY_1_POSTAL},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].unique_id == f"{CITY_1_LAT}, {CITY_1_LON}"
    assert (
        result["title"]
        == f"{CITY_1_NAME} - {CITY_1_ADMIN} ({CITY_1_ADMIN2}) - {CITY_1_COUNTRY}"
    )
    assert result["data"][CONF_LATITUDE] == str(CITY_1_LAT)
    assert result["data"][CONF_LONGITUDE] == str(CITY_1_LON)


async def test_import(hass, client_1):
    """Test import step."""
    # import with all
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_CITY: CITY_1_POSTAL},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result["result"].unique_id == CITY_1_NAME
    assert result["title"] == CITY_1_NAME
    assert result["data"][CONF_CITY] == CITY_1_POSTAL


async def test_abort_if_already_setup(hass, client_1):
    """Test we abort if already setup."""
    MockConfigEntry(
        domain=DOMAIN, data={CONF_CITY: CITY_1_POSTAL}, unique_id=CITY_1_NAME
    ).add_to_hass(hass)

    # Should fail, same CITY same postal code (import)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_CITY: CITY_1_POSTAL},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    # Should fail, same CITY same postal code (flow)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data={CONF_CITY: CITY_1_POSTAL},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_abort_if_already_setup_district(hass, client_2):
    """Test we abort if already setup."""
    MockConfigEntry(
        domain=DOMAIN, data={CONF_CITY: CITY_2_POSTAL_DISTRICT_1}, unique_id=CITY_2_NAME
    ).add_to_hass(hass)

    # Should fail, same CITY different postal code (import)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_IMPORT},
        data={CONF_CITY: CITY_2_POSTAL_DISTRICT_4},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"

    # Should fail, same CITY different postal code (flow)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_2_POSTAL_DISTRICT_4},
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_client_failed(hass):
    """Test when we have errors during client fetch."""
    with patch(
        "homeassistant.components.meteo_france.config_flow.MeteoFranceClient",
        side_effect=MeteoFranceException(),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data={CONF_CITY: CITY_1_POSTAL},
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "unknown"
