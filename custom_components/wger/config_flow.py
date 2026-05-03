"""Config flow for the wger integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WgerAuthError, WgerClient, WgerConnectionError
from .const import (
    CONF_API_KEY,
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_URL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL, default=DEFAULT_URL): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)


class WgerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a wger config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            url = user_input[CONF_URL].strip().rstrip("/")
            if not url.startswith(("http://", "https://")):
                url = f"https://{url}"

            verify_ssl = user_input.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL)
            session = async_get_clientsession(self.hass, verify_ssl=verify_ssl)
            client = WgerClient(
                session=session,
                url=url,
                api_key=user_input[CONF_API_KEY],
                verify_ssl=verify_ssl,
            )

            try:
                await client.async_get_userprofile()
            except WgerAuthError:
                errors["base"] = "invalid_auth"
            except WgerConnectionError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"{url}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"wger ({url})",
                    data={
                        CONF_URL: url,
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_VERIFY_SSL: verify_ssl,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
