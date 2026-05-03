"""Thin async client for the wger REST API."""
from __future__ import annotations

from typing import Any

import aiohttp
from aiohttp import ClientResponseError, ClientTimeout

from .const import API_PATH

REQUEST_TIMEOUT = ClientTimeout(total=20)


class WgerAuthError(Exception):
    """Raised when the API rejects the provided credentials."""


class WgerConnectionError(Exception):
    """Raised when the wger instance is unreachable."""


class WgerClient:
    """Minimal client wrapping the endpoints used by this integration."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        url: str,
        api_key: str,
        verify_ssl: bool = True,
    ) -> None:
        self._session = session
        self._base = f"{url.rstrip('/')}{API_PATH}"
        self._headers = {
            "Authorization": f"Token {api_key}",
            "Accept": "application/json",
        }
        self._verify_ssl = verify_ssl

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self._base}/{path.lstrip('/')}"
        try:
            async with self._session.get(
                url,
                headers=self._headers,
                params=params,
                timeout=REQUEST_TIMEOUT,
                ssl=self._verify_ssl,
            ) as resp:
                if resp.status in (401, 403):
                    raise WgerAuthError(f"Authentication failed ({resp.status})")
                resp.raise_for_status()
                return await resp.json()
        except WgerAuthError:
            raise
        except ClientResponseError as err:
            raise WgerConnectionError(str(err)) from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise WgerConnectionError(str(err)) from err

    async def async_get_userprofile(self) -> dict[str, Any]:
        """Return the authenticated user's profile (validates the API key)."""
        data = await self._get("userprofile/")
        results = data.get("results") or []
        return results[0] if results else data

    async def async_get_latest_weight(self) -> dict[str, Any] | None:
        data = await self._get("weightentry/", params={"ordering": "-date", "limit": 1})
        results = data.get("results") or []
        return results[0] if results else None

    async def async_get_weight_history(self, limit: int = 200) -> list[dict[str, Any]]:
        """Return recent weight entries, newest first."""
        data = await self._get(
            "weightentry/", params={"ordering": "-date", "limit": limit}
        )
        return data.get("results") or []

    async def async_get_measurement_categories(self) -> list[dict[str, Any]]:
        data = await self._get("measurement-category/", params={"limit": 100})
        return data.get("results") or []

    async def async_get_latest_measurement(
        self, category_id: int
    ) -> dict[str, Any] | None:
        data = await self._get(
            "measurement/",
            params={"category": category_id, "ordering": "-date", "limit": 1},
        )
        results = data.get("results") or []
        return results[0] if results else None

    async def async_get_top_workout_log(self) -> dict[str, Any] | None:
        """Return the single workoutlog entry with the heaviest weight."""
        data = await self._get(
            "workoutlog/", params={"ordering": "-weight", "limit": 1}
        )
        results = data.get("results") or []
        return results[0] if results else None

    async def async_get_workout_count(self) -> int:
        data = await self._get("workout/", params={"limit": 1})
        return int(data.get("count", 0))

    async def async_get_session_count(self) -> int:
        data = await self._get("workoutsession/", params={"limit": 1})
        return int(data.get("count", 0))

    async def async_get_latest_session(self) -> dict[str, Any] | None:
        data = await self._get(
            "workoutsession/", params={"ordering": "-date", "limit": 1}
        )
        results = data.get("results") or []
        return results[0] if results else None

    async def async_get_nutrition_plans(self) -> list[dict[str, Any]]:
        data = await self._get("nutritionplan/", params={"limit": 50})
        return data.get("results") or []
