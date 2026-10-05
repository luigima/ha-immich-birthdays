"""Config flow for Immich Birthdays integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_API_KEY, CONF_HOST, CONF_SSL_VERIFY, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="https://your-immich-instance.example.com"): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_SSL_VERIFY, default=True): bool,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input by connecting to Immich API."""
    host = data[CONF_HOST].strip().rstrip("/")
    if not host.startswith(("http://", "https://")):
        host = f"https://{host}"
    data[CONF_HOST] = host

    api_key = data[CONF_API_KEY].strip()
    data[CONF_API_KEY] = api_key
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ImmichBirthdaysOptionsFlowHandler:
        """Get the options flow for this handler."""
        return ImmichBirthdaysOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip().rstrip("/")
            if not host.startswith(("http://", "https://")):
                host = f"https://{host}"
            user_input[CONF_HOST] = host

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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reconfiguring an existing config entry."""
        errors: dict[str, str] = {}
        entry = (
            self._get_reconfigure_entry()
            if hasattr(self, "_get_reconfigure_entry")
            else self.hass.config_entries.async_get_entry(self.context["entry_id"])
        )

        if user_input is not None:
            merged_input = {**entry.data, **user_input}
            try:
                await validate_input(self.hass, merged_input)
                if hasattr(self, "async_update_reload_and_abort"):
                    return self.async_update_reload_and_abort(
                        entry,
                        unique_id=merged_input[CONF_HOST],
                        data_updates=merged_input,
                    )
                self.hass.config_entries.async_update_entry(
                    entry,
                    unique_id=merged_input[CONF_HOST],
                    data=merged_input,
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reconfigure_successful")
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in Immich reconfigure flow")
                errors["base"] = "unknown"

        current_host = entry.data.get(CONF_HOST, "")
        current_api_key = entry.data.get(CONF_API_KEY, "")
        current_ssl_verify = entry.data.get(CONF_SSL_VERIFY, True)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current_host): str,
                vol.Required(CONF_API_KEY, default=current_api_key): str,
                vol.Optional(CONF_SSL_VERIFY, default=current_ssl_verify): bool,
            }
        )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=schema,
            errors=errors,
        )


class ImmichBirthdaysOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Immich Birthdays."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            merged = {
                **self.config_entry.data,
                **self.config_entry.options,
                **user_input,
            }
            try:
                await validate_input(self.hass, merged)
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    unique_id=merged[CONF_HOST],
                    data=merged,
                )
                return self.async_create_entry(title="", data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception in Immich options flow")
                errors["base"] = "unknown"

        current_host = self.config_entry.options.get(
            CONF_HOST, self.config_entry.data.get(CONF_HOST, "")
        )
        current_api_key = self.config_entry.options.get(
            CONF_API_KEY, self.config_entry.data.get(CONF_API_KEY, "")
        )
        current_ssl_verify = self.config_entry.options.get(
            CONF_SSL_VERIFY, self.config_entry.data.get(CONF_SSL_VERIFY, True)
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current_host): str,
                vol.Required(CONF_API_KEY, default=current_api_key): str,
                vol.Optional(CONF_SSL_VERIFY, default=current_ssl_verify): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
