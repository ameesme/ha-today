"""Story coordinator for HA Today integration."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BASE_PROMPT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class StoryData:
    """Data structure for story state."""

    today_story: str = ""
    yesterday_story: str = ""
    today_segments: list[str] = field(default_factory=list)
    pending_events: list[dict[str, Any]] = field(default_factory=list)
    last_update: datetime = field(default_factory=dt_util.now)
    segment_count: int = 0


class StoryCoordinator(DataUpdateCoordinator):
    """Coordinator to manage story generation."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            ),
        )
        self.entry = entry
        self._store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
        self.data = StoryData()
        self._cancel_interval = None
        self._last_date = dt_util.now().date()

    async def async_start(self) -> None:
        """Start the coordinator."""
        _LOGGER.info("Starting story coordinator...")

        # Load persisted data
        await self._load_persisted_data()

        # Set up hourly interval updates
        interval = timedelta(
            minutes=self.entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        )
        self._cancel_interval = async_track_time_interval(
            self.hass, self._async_update_data, interval
        )

        _LOGGER.info(
            "Story coordinator started - interval: %d minutes, pending events: %d, segments: %d",
            interval.total_seconds() / 60,
            len(self.data.pending_events),
            self.data.segment_count,
        )

    async def async_stop(self) -> None:
        """Stop the coordinator."""
        if self._cancel_interval:
            self._cancel_interval()
        await self._persist_data()

    async def manual_generate(self) -> None:
        """Manually trigger story generation."""
        _LOGGER.info("=== Manual generation triggered ===")
        await self._async_update_data()

    async def add_event(self, event_data: dict[str, Any]) -> None:
        """Add an event to the pending buffer."""
        event = {
            "timestamp": dt_util.now(),
            "event": event_data.get("event", ""),
            "entity_id": event_data.get("entity_id"),
            "metadata": event_data.get("metadata", {}),
        }

        self.data.pending_events.append(event)
        _LOGGER.info(
            "Event added: '%s' (entity: %s, total pending: %d)",
            event["event"],
            event["entity_id"] or "none",
            len(self.data.pending_events),
        )

        # Persist immediately to prevent data loss on reboot
        await self._persist_data()
        _LOGGER.debug("Event persisted to storage")

        # Notify listeners that data has changed
        self.async_set_updated_data(self.data)

    async def _async_update_data(self, *args) -> StoryData:
        """Generate next story segment (called hourly)."""
        _LOGGER.info("=== Story update triggered ===")
        current_date = dt_util.now().date()

        # Check for midnight rollover
        if current_date != self._last_date:
            _LOGGER.info("Midnight rollover detected: %s -> %s", self._last_date, current_date)
            await self._handle_midnight_rollover()
            self._last_date = current_date

        # Only generate segment if we have pending events
        if not self.data.pending_events:
            _LOGGER.warning("No pending events in buffer - skipping segment generation")
            return self.data

        _LOGGER.info("Processing %d pending events for story generation", len(self.data.pending_events))

        # Generate story segment
        await self._generate_segment()

        return self.data

    async def _generate_segment(self) -> None:
        """Generate a story segment from pending events."""
        try:
            # Build the prompt
            base_prompt = self.entry.data.get(CONF_BASE_PROMPT, "")
            _LOGGER.debug("Using base prompt: %s...", base_prompt[:100])

            formatted_prompt = self._build_prompt(
                base_prompt, self.data.pending_events, self.data.today_segments
            )

            _LOGGER.info(
                "Generating segment %d with %d events",
                self.data.segment_count + 1,
                len(self.data.pending_events),
            )
            _LOGGER.info("=== FULL PROMPT ===\n%s\n=== END PROMPT ===", formatted_prompt)

            # Call AI task service
            _LOGGER.info("Calling ai_task.generate_data service...")
            response = await self.hass.services.async_call(
                "ai_task",
                "generate_data",
                {
                    "task_name": "Generate story segment",
                    "instructions": formatted_prompt,
                },
                blocking=True,
                return_response=True,
            )

            _LOGGER.info("AI service raw response: %s", response)
            _LOGGER.info("Response type: %s, keys: %s", type(response), response.keys() if isinstance(response, dict) else "not a dict")

            # Extract segment from response - try different possible keys
            segment = None
            if isinstance(response, dict):
                # Try common response keys (ai_task uses "data")
                segment = (
                    response.get("data") or
                    response.get("text") or
                    response.get("response") or
                    response.get("content") or
                    response.get("output") or
                    response.get("result")
                )
            elif isinstance(response, str):
                segment = response

            if segment:
                segment = segment.strip()

            if not segment:
                _LOGGER.error(
                    "AI service returned empty segment! Response was: %s",
                    response
                )
                return

            _LOGGER.info("Generated segment: '%s' (%d chars)", segment[:50], len(segment))

            # Append segment to today's story (concatenate with space)
            self.data.today_segments.append(segment)
            self.data.today_story = " ".join(self.data.today_segments)
            self.data.segment_count += 1
            self.data.last_update = dt_util.now()

            # Clear pending events after successful generation
            events_processed = len(self.data.pending_events)
            self.data.pending_events.clear()

            _LOGGER.info(
                "✓ Story segment %d completed - processed %d events, story length: %d chars",
                self.data.segment_count,
                events_processed,
                len(self.data.today_story),
            )

            # Persist the updated state
            await self._persist_data()

        except Exception as err:
            _LOGGER.error("Failed to generate story segment: %s", err, exc_info=True)
            # Events remain in pending_events buffer for retry on next interval

    def _build_prompt(
        self,
        base_prompt: str,
        events: list[dict[str, Any]],
        previous_segments: list[str],
    ) -> str:
        """Build the LLM prompt from template."""
        # Format events
        events_text = "\n".join(
            [
                f"- {evt['timestamp'].strftime('%H:%M')}: {evt['event']}"
                + (f" (entity: {evt['entity_id']})" if evt.get("entity_id") else "")
                for evt in events
            ]
        )

        # Format story so far (concatenated segments)
        story_so_far = " ".join(previous_segments) if previous_segments else "The day begins."

        # Fill template
        return base_prompt.format(events=events_text, previous_segments=story_so_far)

    async def _handle_midnight_rollover(self) -> None:
        """Handle transition to a new day."""
        _LOGGER.info("Midnight rollover: saving today's story to yesterday")

        # Move today's story to yesterday
        self.data.yesterday_story = self.data.today_story

        # Reset today's story
        self.data.today_story = ""
        self.data.today_segments.clear()
        self.data.segment_count = 0
        self.data.last_update = dt_util.now()

        # Note: pending_events are NOT cleared - they carry over to the new day
        # This ensures events submitted late at night are included in next segment

        await self._persist_data()

    async def _load_persisted_data(self) -> None:
        """Load story data from storage."""
        data = await self._store.async_load()

        if data:
            # Restore pending events with datetime objects
            pending_events = []
            for evt in data.get("pending_events", []):
                evt_copy = evt.copy()
                evt_copy["timestamp"] = datetime.fromisoformat(evt["timestamp"])
                pending_events.append(evt_copy)

            self.data = StoryData(
                today_story=data.get("today_story", ""),
                yesterday_story=data.get("yesterday_story", ""),
                today_segments=data.get("today_segments", []),
                pending_events=pending_events,
                last_update=datetime.fromisoformat(data["last_update"]),
                segment_count=data.get("segment_count", 0),
            )

            _LOGGER.info(
                "Loaded persisted data: %d segments, %d pending events",
                self.data.segment_count,
                len(self.data.pending_events),
            )
        else:
            _LOGGER.info("No persisted data found, starting fresh")
            self.data = StoryData()

        # Update last_date tracking
        self._last_date = dt_util.now().date()

    async def _persist_data(self) -> None:
        """Save story data to storage."""
        # Convert pending events to serializable format
        pending_events = []
        for evt in self.data.pending_events:
            evt_copy = evt.copy()
            evt_copy["timestamp"] = evt["timestamp"].isoformat()
            pending_events.append(evt_copy)

        await self._store.async_save(
            {
                "today_story": self.data.today_story,
                "yesterday_story": self.data.yesterday_story,
                "today_segments": self.data.today_segments,
                "pending_events": pending_events,
                "last_update": self.data.last_update.isoformat(),
                "segment_count": self.data.segment_count,
            }
        )

        _LOGGER.debug("Story data persisted")
