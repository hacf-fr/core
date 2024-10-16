"""Tests for the Spotify initialization."""

from unittest.mock import MagicMock

import pytest
from spotipy import SpotifyException

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("setup_credentials")
async def test_setup(
    hass: HomeAssistant,
    mock_spotify: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the Spotify setup."""
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.usefixtures("setup_credentials")
@pytest.mark.parametrize(
    "method",
    [
        "me",
        "devices",
    ],
)
async def test_setup_with_required_calls_failing(
    hass: HomeAssistant,
    mock_spotify: MagicMock,
    mock_config_entry: MockConfigEntry,
    method: str,
) -> None:
    """Test the Spotify setup with required calls failing."""
    getattr(mock_spotify.return_value, method).side_effect = SpotifyException(
        400, "Bad Request", "Bad Request"
    )
    mock_config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)


@pytest.mark.usefixtures("setup_credentials")
async def test_no_current_user(
    hass: HomeAssistant,
    mock_spotify: MagicMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test the Spotify setup with required calls failing."""
    mock_spotify.return_value.me.return_value = None
    mock_config_entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
