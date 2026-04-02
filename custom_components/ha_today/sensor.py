"""Sensor platform for HA Today integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_EVENTS_COUNT,
    ATTR_LAST_SEGMENT,
    ATTR_SEGMENT_COUNT,
    ATTR_STORY_TEXT,
    DOMAIN,
)
from .coordinator import StoryCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up HA Today sensors."""
    coordinator: StoryCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            StorySensor(coordinator, entry),
            PendingEventsSensor(coordinator, entry),
            LastGeneratedSensor(coordinator, entry),
        ]
    )


class StorySensor(CoordinatorEntity, SensorEntity):
    """Sensor for the home story (last 24 hours)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:book-open-variant"

    def __init__(self, coordinator: StoryCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_story"
        self._attr_name = "Story"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        count = len(self.coordinator.data.story_entries)
        if count > 0:
            return f"{count} entries"
        return "No entries yet"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {
            ATTR_STORY_TEXT: self.coordinator.data.recent_story,
            ATTR_SEGMENT_COUNT: len(self.coordinator.data.story_entries),
            ATTR_EVENTS_COUNT: len(self.coordinator.data.pending_events),
        }

        # Add last segment if available
        if self.coordinator.data.story_entries:
            attrs[ATTR_LAST_SEGMENT] = self.coordinator.data.story_entries[-1]["content"]

        return attrs


class PendingEventsSensor(CoordinatorEntity, SensorEntity):
    """Sensor for pending events count."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:clipboard-list"
    _attr_state_class = "measurement"

    def __init__(self, coordinator: StoryCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_pending_events"
        self._attr_name = "Pending Events"

    @property
    def native_value(self) -> int:
        """Return the count of pending events."""
        return len(self.coordinator.data.pending_events)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the pending events as attributes."""
        return {
            "events": [
                {
                    "time": evt["timestamp"].strftime("%H:%M:%S"),
                    "event": evt["event"],
                }
                for evt in self.coordinator.data.pending_events
            ]
        }


class LastGeneratedSensor(CoordinatorEntity, SensorEntity):
    """Sensor for last generation timestamp."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: StoryCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_generated"
        self._attr_name = "Last Generated"

    @property
    def native_value(self) -> datetime | None:
        """Return the timestamp of last generation."""
        return self.coordinator.data.last_generation_time
