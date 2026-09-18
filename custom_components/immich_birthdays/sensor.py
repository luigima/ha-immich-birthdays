"""Sensors for Immich Birthdays integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_AGE,
    ATTR_BIRTH_DATE,
    ATTR_DAYS_UNTIL,
    ATTR_IS_FAVORITE,
    ATTR_IS_TODAY,
    ATTR_NEXT_AGE,
    ATTR_NEXT_BIRTHDAY,
    ATTR_PERSON_ID,
    ATTR_TODAY_BIRTHDAYS,
    ATTR_UPCOMING_BIRTHDAYS,
    DOMAIN,
)
from .coordinator import ImmichBirthdaysCoordinator, ImmichPerson

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Immich birthday sensors based on config entry."""
    coordinator: ImmichBirthdaysCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[SensorEntity] = [
        ImmichNextBirthdaysSensor(coordinator, entry),
    ]

    for person in coordinator.data:
        entities.append(ImmichPersonBirthdaySensor(coordinator, entry, person.id))

    async_add_entities(entities)


class ImmichPersonBirthdaySensor(CoordinatorEntity[ImmichBirthdaysCoordinator], SensorEntity):
    """Sensor for an individual person's birthday."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ImmichBirthdaysCoordinator,
        entry: ConfigEntry,
        person_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.person_id = person_id
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{entry.entry_id}_person_{person_id}"

    @property
    def _person(self) -> ImmichPerson | None:
        """Find the matching person data from coordinator."""
        for p in self.coordinator.data:
            if p.id == self.person_id:
                return p
        return None

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        person = self._person
        return f"{person.name} Birthday" if person else "Birthday"

    @property
    def native_value(self) -> str | None:
        """Return state of sensor (e.g. 'Today', 'Tomorrow', 'in 5 days')."""
        person = self._person
        if not person:
            return None

        if person.is_today:
            return "Today"
        if person.days_until == 1:
            return "in 1 day"
        return f"in {person.days_until} days"

    @property
    def entity_picture(self) -> str | None:
        """Return the person's face thumbnail URL as the entity picture."""
        person = self._person
        return person.thumbnail_url if person else None

    @property
    def icon(self) -> str:
        """Return icon depending on whether it is today."""
        person = self._person
        if person and person.is_today:
            return "mdi:party-popper"
        return "mdi:cake-variant"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed birthday attributes."""
        person = self._person
        if not person:
            return {}

        return {
            ATTR_PERSON_ID: person.id,
            "name": person.name,
            ATTR_BIRTH_DATE: str(person.birth_date),
            ATTR_NEXT_BIRTHDAY: str(person.next_birthday),
            ATTR_DAYS_UNTIL: person.days_until,
            ATTR_AGE: person.current_age,
            ATTR_NEXT_AGE: person.turning_age,
            ATTR_IS_TODAY: person.is_today,
            ATTR_IS_FAVORITE: person.is_favorite,
        }


class ImmichNextBirthdaysSensor(CoordinatorEntity[ImmichBirthdaysCoordinator], SensorEntity):
    """Aggregate sensor reporting upcoming birthdays and celebrating today."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:calendar-heart"

    def __init__(
        self,
        coordinator: ImmichBirthdaysCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the aggregate sensor."""
        super().__init__(coordinator)
        self._attr_name = "Next Birthdays"
        self._attr_unique_id = f"{entry.entry_id}_next_birthdays"

    @property
    def native_value(self) -> str | None:
        """Return summary of who is next or who has birthday today."""
        if not self.coordinator.data:
            return "No birthdays"

        today_people = [p.name for p in self.coordinator.data if p.is_today]
        if today_people:
            return f"{', '.join(today_people)} (Today! 🎉)"

        first = self.coordinator.data[0]
        return f"{first.name} ({first.native_value if hasattr(first, 'native_value') else f'in {first.days_until} days'})"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return list of upcoming birthdays."""
        upcoming = []
        today = []

        for p in self.coordinator.data:
            info = {
                "name": p.name,
                "birth_date": str(p.birth_date),
                "next_birthday": str(p.next_birthday),
                "days_until": p.days_until,
                "age": p.current_age,
                "turning_age": p.turning_age,
                "is_today": p.is_today,
                "thumbnail_url": p.thumbnail_url,
            }
            upcoming.append(info)
            if p.is_today:
                today.append(info)

        return {
            ATTR_TODAY_BIRTHDAYS: today,
            ATTR_UPCOMING_BIRTHDAYS: upcoming,
            "total_birthdays": len(upcoming),
        }
