"""DataUpdateCoordinator for Immich Birthdays."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


def _get_next_birthday(birth_date: date, today: date) -> tuple[date, int, int]:
    """Calculate next birthday, days until, and turning age handling leap years."""
    try:
        bday_this_year = birth_date.replace(year=today.year)
    except ValueError:
        # Handle Feb 29 in non-leap year
        bday_this_year = date(today.year, 2, 28)

    if bday_this_year < today:
        target_year = today.year + 1
        try:
            next_bday = birth_date.replace(year=target_year)
        except ValueError:
            next_bday = date(target_year, 2, 28)
    else:
        next_bday = bday_this_year

    days_until = (next_bday - today).days
    turning_age = next_bday.year - birth_date.year
    return next_bday, days_until, turning_age


@dataclass
class ImmichPerson:
    """Class representing an Immich person with birthday details."""

    id: str
    name: str
    birth_date: date
    next_birthday: date
    days_until: int
    current_age: int
    turning_age: int
    is_today: bool
    is_favorite: bool
    thumbnail_url: str


class ImmichBirthdaysCoordinator(DataUpdateCoordinator[list[ImmichPerson]]):
    """Coordinator to fetch people and birthdays from Immich."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        api_key: str,
        ssl_verify: bool = True,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.host = host.rstrip("/")
        self.api_key = api_key
        self.ssl_verify = ssl_verify
        self._thumbnail_cache: dict[str, bytes] = {}

    async def _async_update_data(self) -> list[ImmichPerson]:
        """Fetch all people from Immich and filter those with birthdays."""
        session = async_get_clientsession(self.hass, verify_ssl=self.ssl_verify)
        headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json",
        }

        url = f"{self.host}/api/people"
        try:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    raise UpdateFailed(f"Immich API returned status {resp.status}")
                data = await resp.json()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Immich: {err}") from err

        people_raw = data.get("people", [])
        today = dt_util.now().date()
        result: list[ImmichPerson] = []

        for p in people_raw:
            birth_date_str = p.get("birthDate")
            if not birth_date_str or p.get("isHidden"):
                continue

            try:
                b_date = datetime.strptime(birth_date_str[:10], "%Y-%m-%d").date()
            except ValueError:
                continue

            next_bday, days_until, turning_age = _get_next_birthday(b_date, today)

            # Calculate current age
            current_age = (
                today.year
                - b_date.year
                - ((today.month, today.day) < (b_date.month, b_date.day))
            )

            person = ImmichPerson(
                id=p["id"],
                name=p.get("name") or "Unnamed",
                birth_date=b_date,
                next_birthday=next_bday,
                days_until=days_until,
                current_age=current_age,
                turning_age=turning_age,
                is_today=(days_until == 0),
                is_favorite=bool(p.get("isFavorite", False)),
                thumbnail_url=f"/api/immich_birthdays/thumbnail/{p['id']}",
            )
            result.append(person)

        # Sort by days until birthday ascending
        result.sort(key=lambda x: (x.days_until, x.name))
        return result

    async def async_get_thumbnail(self, person_id: str) -> bytes | None:
        """Fetch and cache face thumbnail for a person."""
        if person_id in self._thumbnail_cache:
            return self._thumbnail_cache[person_id]

        session = async_get_clientsession(self.hass, verify_ssl=self.ssl_verify)
        headers = {
            "x-api-key": self.api_key,
        }
        url = f"{self.host}/api/people/{person_id}/thumbnail"

        try:
            async with session.get(url, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    self._thumbnail_cache[person_id] = content
                    return content
                _LOGGER.debug(
                    "Thumbnail request for person %s failed with status %s",
                    person_id,
                    resp.status,
                )
        except Exception as err:
            _LOGGER.warning("Error fetching thumbnail for person %s: %err", person_id, err)

        return None
