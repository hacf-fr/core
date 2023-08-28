"""The EGS integration."""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import TypedDict

from epicstore_api import EpicGamesStoreAPI

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN

SCAN_INTERVAL = timedelta(days=1)

_LOGGER = logging.getLogger(__name__)


class GameData(TypedDict):
    """Game fields."""

    title: str
    publisher: str
    url: str
    img_portrait: str | None
    img_landscape: str | None
    original_price: str


class FreeGameData(TypedDict):
    """Free game fields."""

    start_at: datetime
    end_at: datetime
    games: list[GameData]


class EGSUpdateCoordinatorData(TypedDict):
    """Formatted API response."""

    free_games: FreeGameData
    next_free_games: FreeGameData


class EGSUpdateCoordinator(DataUpdateCoordinator[EGSUpdateCoordinatorData]):
    """Class to manage fetching data from the Epic Game Store."""

    def __init__(
        self, hass: HomeAssistant, api: EpicGamesStoreAPI, locale: str
    ) -> None:
        """Initialize."""
        self._api = api
        self.locale = locale

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self) -> EGSUpdateCoordinatorData:
        """Update data via library."""
        try:
            raw_data = await self.hass.async_add_executor_job(self._api.get_free_games)
        except Exception as error:
            raise UpdateFailed(error) from error

        _LOGGER.debug(raw_data)

        promo_games = sorted(
            filter(
                lambda g: g.get("promotions")
                and (
                    (
                        g["promotions"]["promotionalOffers"]
                        and g["price"]["totalPrice"]["discountPrice"] == 0
                    )
                    or (g["promotions"]["upcomingPromotionalOffers"])
                ),
                raw_data["data"]["Catalog"]["searchStore"]["elements"],
            ),
            key=lambda g: g["title"],
        )

        return_data: EGSUpdateCoordinatorData = self.data or {}
        for game in promo_games:
            game_title = game["title"]
            game_publisher = game["seller"]["name"]
            game_url = f"https://store.epicgames.com/{self.locale}/p/{game['catalogNs']['mappings'][0]['pageSlug']}"
            game_img_portrait = None
            game_img_landscape = None

            for image in game["keyImages"]:
                if image["type"] == "OfferImageTall":
                    game_img_portrait = image["url"]
                if image["type"] == "OfferImageWide":
                    game_img_landscape = image["url"]

            game_price = game["price"]["totalPrice"]["fmtPrice"]["originalPrice"]
            game_promotions = game["promotions"]["promotionalOffers"]
            upcoming_promotions = game["promotions"]["upcomingPromotionalOffers"]

            is_next = False
            promotion_data = {}
            if game_promotions and game["price"]["totalPrice"]["discountPrice"] == 0:
                promotion_data = game_promotions[0]["promotionalOffers"][0]
            elif not game_promotions and upcoming_promotions:
                is_next = True
                promotion_data = upcoming_promotions[0]["promotionalOffers"][0]

            if promotion_data:
                free_games: list[GameData] = []
                free_games += return_data.get(
                    "next_free_games" if is_next else "free_games", []
                )
                free_game = FreeGameData(
                    start_at=dt_util.parse_datetime(promotion_data["startDate"]),
                    end_at=dt_util.parse_datetime(promotion_data["endDate"]),
                    games=[
                        **return_data.get(
                            "next_free_games" if is_next else "free_games", {}
                        ).get("games", [])
                    ],
                )
                free_game["games"].append(
                    GameData(
                        title=game_title,
                        publisher=game_publisher,
                        url=game_url,
                        img_portrait=game_img_portrait,
                        img_landscape=game_img_landscape,
                        original_price=game_price.replace("\xa0", " "),
                    )
                )
                if is_next:
                    return_data["next_free_games"] = free_game
                else:
                    return_data["free_games"] = free_game

        _LOGGER.debug(return_data)
        return return_data
