"""The Immich Birthdays integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_HOST, CONF_SSL_VERIFY, DOMAIN
from .coordinator import ImmichBirthdaysCoordinator
from .view import ImmichThumbnailView

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CALENDAR]
VIEW_REGISTERED_KEY = f"{DOMAIN}_view_registered"


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Immich Birthdays from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.options.get(CONF_HOST, entry.data.get(CONF_HOST))
    api_key = entry.options.get(CONF_API_KEY, entry.data.get(CONF_API_KEY))
    ssl_verify = entry.options.get(CONF_SSL_VERIFY, entry.data.get(CONF_SSL_VERIFY, True))

    coordinator = ImmichBirthdaysCoordinator(
        hass=hass,
        host=host,
        api_key=api_key,
        ssl_verify=ssl_verify,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # Register the thumbnail HTTP proxy view once
    if not hass.data[DOMAIN].get(VIEW_REGISTERED_KEY):
        hass.http.register_view(ImmichThumbnailView(hass))
        hass.data[DOMAIN][VIEW_REGISTERED_KEY] = True

    # Register update listener to reload when options are changed
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
