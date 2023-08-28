"""Test the Epic Games Store config flow."""
from http.client import HTTPException
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.components.epic_games_store.config_flow import get_default_locale
from homeassistant.components.epic_games_store.const import CONF_LOCALE, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .const import DATA_ERROR_WRONG_COUNTRY, DATA_FREE_GAMES, MOCK_LOCALE


async def test_default_locale(hass: HomeAssistant) -> None:
    """Test we get the form."""
    hass.config.language = "fr"
    hass.config.country = "FR"
    assert get_default_locale(hass) == "fr"

    hass.config.language = "es"
    hass.config.country = "ES"
    assert get_default_locale(hass) == "es-ES"

    hass.config.language = "en"
    hass.config.country = "AZ"
    assert get_default_locale(hass) == "en-US"


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.epic_games_store.config_flow.EpicGamesStoreAPI.get_free_games",
        return_value=DATA_FREE_GAMES,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LOCALE: MOCK_LOCALE,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == f"Epic Games Store {MOCK_LOCALE}"
    assert result2["data"] == {
        CONF_LOCALE: MOCK_LOCALE,
    }


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.epic_games_store.config_flow.EpicGamesStoreAPI.get_free_games",
        side_effect=HTTPException,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LOCALE: MOCK_LOCALE,
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "unknown"}


async def test_form_cannot_connect_wrong_param(hass: HomeAssistant) -> None:
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.epic_games_store.config_flow.EpicGamesStoreAPI.get_free_games",
        return_value=DATA_ERROR_WRONG_COUNTRY,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LOCALE: MOCK_LOCALE,
            },
        )

    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
