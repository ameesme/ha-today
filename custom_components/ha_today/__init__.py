"""The HA Today integration."""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
import homeassistant.helpers.config_validation as cv

from .const import DOMAIN, SERVICE_COMMIT_EVENT
from .coordinator import StoryCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Service schema
SERVICE_COMMIT_EVENT_SCHEMA = vol.Schema(
    {
        vol.Required("event"): cv.string,
        vol.Optional("entity_id"): cv.entity_id,
        vol.Optional("metadata"): dict,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Today from a config entry."""
    # Initialize coordinator
    coordinator = StoryCoordinator(hass, entry)
    await coordinator.async_start()

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register service (only once for all entries)
    if not hass.services.has_service(DOMAIN, SERVICE_COMMIT_EVENT):

        async def handle_commit_event(call: ServiceCall) -> None:
            """Handle the commit_event service call."""
            # Get all coordinators and add event to each
            for coordinator_entry_id, coordinator in hass.data[DOMAIN].items():
                if isinstance(coordinator, StoryCoordinator):
                    await coordinator.add_event(call.data)

        hass.services.async_register(
            DOMAIN,
            SERVICE_COMMIT_EVENT,
            handle_commit_event,
            schema=SERVICE_COMMIT_EVENT_SCHEMA,
        )

        _LOGGER.info("Registered %s.%s service", DOMAIN, SERVICE_COMMIT_EVENT)

    # Forward setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Stop coordinator
        coordinator: StoryCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_stop()

        # Remove coordinator from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)

        # Remove service if this is the last entry
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_COMMIT_EVENT)
            _LOGGER.info("Removed %s.%s service", DOMAIN, SERVICE_COMMIT_EVENT)

    return unload_ok
