"""Data update coordinator for wger."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WgerAuthError, WgerClient, WgerConnectionError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

BODY_FAT_KEYWORDS = ("body fat", "bodyfat", "fat %", "fat%", "bf%", "אחוז שומן", "שומן")


def _parse_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _find_body_fat_category(categories: list[dict[str, Any]]) -> dict[str, Any] | None:
    for cat in categories:
        name = (cat.get("name") or "").strip().lower()
        if any(kw in name for kw in BODY_FAT_KEYWORDS):
            return cat
    return None


def _compute_weight_deltas(history: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute delta vs previous entry and vs the entry closest to ~30d ago."""
    parsed = []
    for entry in history:
        w = _parse_float(entry.get("weight"))
        d = _parse_date(entry.get("date"))
        if w is not None and d is not None:
            parsed.append((d, w, entry))
    if not parsed:
        return {"delta_last": None, "delta_30d": None}

    parsed.sort(key=lambda item: item[0], reverse=True)
    latest_date, latest_weight, _ = parsed[0]

    delta_last = None
    if len(parsed) >= 2:
        _, prev_weight, _ = parsed[1]
        delta_last = round(latest_weight - prev_weight, 2)

    delta_30d = None
    target = latest_date - timedelta(days=30)
    candidates = [item for item in parsed[1:] if item[0] <= target]
    reference = candidates[0] if candidates else (parsed[-1] if len(parsed) > 1 else None)
    if reference is not None:
        delta_30d = round(latest_weight - reference[1], 2)

    return {
        "delta_last": delta_last,
        "delta_30d": delta_30d,
        "delta_last_from_date": parsed[1][0].isoformat() if len(parsed) >= 2 else None,
        "delta_30d_from_date": reference[0].isoformat() if reference else None,
    }


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
        self._body_fat_category_id: int | None = None
        self._body_fat_lookup_done = False

    async def _resolve_body_fat_category(self) -> int | None:
        if self._body_fat_lookup_done:
            return self._body_fat_category_id
        try:
            categories = await self.client.async_get_measurement_categories()
        except (WgerAuthError, WgerConnectionError) as err:
            _LOGGER.debug("Could not list measurement categories: %s", err)
            return None
        match = _find_body_fat_category(categories)
        if match:
            self._body_fat_category_id = int(match["id"])
        self._body_fat_lookup_done = True
        return self._body_fat_category_id

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            profile = await self.client.async_get_userprofile()
            weight_history = await self.client.async_get_weight_history()
            workout_count = await self.client.async_get_workout_count()
            session_count = await self.client.async_get_session_count()
            latest_session = await self.client.async_get_latest_session()
            nutrition_plans = await self.client.async_get_nutrition_plans()
            top_log = await self.client.async_get_top_workout_log()
        except WgerAuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except WgerConnectionError as err:
            raise UpdateFailed(f"Connection error: {err}") from err

        latest_weight = weight_history[0] if weight_history else None
        deltas = _compute_weight_deltas(weight_history)

        height_cm = _parse_float((profile or {}).get("height"))
        latest_weight_kg = _parse_float((latest_weight or {}).get("weight"))
        bmi = None
        if height_cm and height_cm > 0 and latest_weight_kg is not None:
            height_m = height_cm / 100.0
            bmi = round(latest_weight_kg / (height_m * height_m), 1)

        body_fat_entry: dict[str, Any] | None = None
        category_id = await self._resolve_body_fat_category()
        if category_id is not None:
            try:
                body_fat_entry = await self.client.async_get_latest_measurement(
                    category_id
                )
            except (WgerAuthError, WgerConnectionError) as err:
                _LOGGER.debug("Could not fetch body fat measurement: %s", err)

        return {
            "profile": profile,
            "latest_weight": latest_weight,
            "weight_delta_last": deltas["delta_last"],
            "weight_delta_30d": deltas["delta_30d"],
            "weight_delta_last_from_date": deltas.get("delta_last_from_date"),
            "weight_delta_30d_from_date": deltas.get("delta_30d_from_date"),
            "bmi": bmi,
            "body_fat": body_fat_entry,
            "workout_count": workout_count,
            "session_count": session_count,
            "latest_session": latest_session,
            "nutrition_plans": nutrition_plans,
            "top_log": top_log,
        }
