"""Calendar platform for Immich Birthdays."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ImmichBirthdaysCoordinator, ImmichPerson

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Immich birthdays calendar entity."""
    coordinator: ImmichBirthdaysCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([ImmichBirthdayCalendar(coordinator, entry)])


class ImmichBirthdayCalendar(CoordinatorEntity[ImmichBirthdaysCoordinator], CalendarEntity):
    """A calendar entity providing all birthdays from Immich."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-star"

    def __init__(
        self,
        coordinator: ImmichBirthdaysCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_name = "Birthdays"
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming birthday event."""
        if not self.coordinator.data:
            return None

        # Coordinator is already sorted by days_until ascending
        next_person: ImmichPerson = self.coordinator.data[0]
        start_dt = datetime.combine(next_person.next_birthday, datetime.min.time())
        end_dt = start_dt + timedelta(days=1)

        return CalendarEvent(
            summary=f"{next_person.name} ({next_person.turning_age})",
            start=start_dt.date(),
            end=end_dt.date(),
            description=f"Born: {next_person.birth_date} (turns {next_person.turning_age})",
            uid=f"immich_bday_{next_person.id}_{next_person.next_birthday.year}",
        )

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within the given datetime window."""
        events: list[CalendarEvent] = []
        if not self.coordinator.data:
            return events

        start_year = start_date.year
        end_year = end_date.year

        for person in self.coordinator.data:
            for yr in range(start_year, end_year + 1):
                try:
                    bday = person.birth_date.replace(year=yr)
                except ValueError:
                    # Leap year Feb 29 adjustment
                    bday = date(yr, 2, 28)

                bday_dt = datetime.combine(bday, datetime.min.time())
                if start_date <= bday_dt <= end_date:
                    turning_age = yr - person.birth_date.year
                    events.append(
                        CalendarEvent(
                            summary=f"{person.name} ({turning_age})",
                            start=bday,
                            end=bday + timedelta(days=1),
                            description=f"Born: {person.birth_date} (turns {turning_age})",
                            uid=f"immich_bday_{person.id}_{yr}",
                        )
                    )

        events.sort(key=lambda ev: ev.start)
        return events
