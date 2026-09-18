"""Config flow for Immich Birthdays integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_HOST, CONF_SSL_VERIFY, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="http://192.168.1.100:2283"): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_SSL_VERIFY, default=True): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input by connecting to Immich API."""
    host = data[CONF_HOST].rstrip("/")
    api_key = data[CONF_API_KEY]
    ssl_verify = data.get(CONF_SSL_VERIFY, True)

    session = async_get_clientsession(hass, verify_ssl=ssl_verify)
    headers = {"x-api-key": api_key, "Accept": "application/json"}

    url = f"{host}/api/people"
    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status == 401:
                raise InvalidAuth
            if resp.status != 200:
                raise CannotConnect(f"Unexpected status: {resp.status}")
            result = await resp.json()
    except aiohttp.ClientError as err:
        raise CannotConnect(str(err)) from err

    people_count = len(result.get("people", []))
    return {"title": "Immich Birthdays", "people_count": people_count}


class ImmichBirthdaysConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Immich Birthdays."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].rstrip("/")
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in Immich config flow")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
