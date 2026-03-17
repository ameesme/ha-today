"""Sensor platform for HA Today integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    RestoreSensor,
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
            TodayStorySensor(coordinator, entry),
            YesterdayStorySensor(coordinator, entry),
            LastUpdatedSensor(coordinator, entry),
        ]
    )


class TodayStorySensor(CoordinatorEntity, RestoreSensor):
    """Sensor for today's story."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:book-open-variant"

    def __init__(self, coordinator: StoryCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_today_story"
        self._attr_name = "Today Story"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if self.coordinator.data.segment_count > 0:
            return f"{self.coordinator.data.segment_count} segments"
        return "No story yet"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {
            ATTR_STORY_TEXT: self.coordinator.data.today_story,
            ATTR_SEGMENT_COUNT: self.coordinator.data.segment_count,
            ATTR_EVENTS_COUNT: len(self.coordinator.data.pending_events),
        }

        # Add last segment if available
        if self.coordinator.data.today_segments:
            attrs[ATTR_LAST_SEGMENT] = self.coordinator.data.today_segments[-1]

        return attrs

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()

        # Restore previous state if available
        if (last_state := await self.async_get_last_state()) is not None:
            _LOGGER.debug("Restored state for today's story sensor")


class YesterdayStorySensor(CoordinatorEntity, RestoreSensor):
    """Sensor for yesterday's story."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:book-open-page-variant"

    def __init__(self, coordinator: StoryCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_yesterday_story"
        self._attr_name = "Yesterday Story"

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        if self.coordinator.data.yesterday_story:
            return "Completed"
        return "No story yet"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return {ATTR_STORY_TEXT: self.coordinator.data.yesterday_story}

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()

        # Restore previous state if available
        if (last_state := await self.async_get_last_state()) is not None:
            _LOGGER.debug("Restored state for yesterday's story sensor")


class LastUpdatedSensor(CoordinatorEntity, SensorEntity):
    """Sensor for last update timestamp."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: StoryCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_updated"
        self._attr_name = "Last Updated"

    @property
    def native_value(self) -> datetime:
        """Return the timestamp of last update."""
        return self.coordinator.data.last_update
