"""HTTP view to proxy Immich person thumbnails into Home Assistant."""

from __future__ import annotations

import logging
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import ImmichBirthdaysCoordinator

_LOGGER = logging.getLogger(__name__)


class ImmichThumbnailView(HomeAssistantView):
    """View to serve Immich person thumbnails as entity pictures."""

    url = "/api/immich_birthdays/thumbnail/{person_id}"
    name = "api:immich_birthdays:thumbnail"
    requires_auth = False  # Allows <img> tags in Lovelace / Bubble Card to load avatars

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the view."""
        self.hass = hass

    async def get(self, request: web.Request, person_id: str) -> web.Response:
        """Handle request for person thumbnail."""
        # Retrieve coordinator from hass.data
        coordinators: list[ImmichBirthdaysCoordinator] = [
            entry_data["coordinator"]
            for entry_data in self.hass.data.get(DOMAIN, {}).values()
            if isinstance(entry_data, dict) and "coordinator" in entry_data
        ]

        if not coordinators:
            return web.Response(status=404, text="Immich integration not loaded")

        # Try each coordinator to locate the thumbnail
        for coordinator in coordinators:
            image_bytes = await coordinator.async_get_thumbnail(person_id)
            if image_bytes:
                return web.Response(
                    body=image_bytes,
                    content_type="image/jpeg",
                    headers={
                        "Cache-Control": "public, max-age=86400",  # Cache for 24 hours
                    },
                )

        return web.Response(status=404, text="Thumbnail not found")
