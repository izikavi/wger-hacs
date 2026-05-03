"""Data update coordinator for wger."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WgerAuthError, WgerClient, WgerConnectionError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class WgerDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch data from wger on a fixed interval."""

    def __init__(self, hass: HomeAssistant, client: WgerClient, entry_id: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry_id}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            profile = await self.client.async_get_userprofile()
            latest_weight = await self.client.async_get_latest_weight()
            workout_count = await self.client.async_get_workout_count()
            session_count = await self.client.async_get_session_count()
            latest_session = await self.client.async_get_latest_session()
            nutrition_plans = await self.client.async_get_nutrition_plans()
        except WgerAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except WgerConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err

        return {
            "profile": profile,
            "latest_weight": latest_weight,
            "workout_count": workout_count,
            "session_count": session_count,
            "latest_session": latest_session,
            "nutrition_plans": nutrition_plans,
        }
