"""Story coordinator for HA Today integration."""
from __future__ import annotations

import aiosqlite
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BASE_PROMPT,
    DEFAULT_BASE_PROMPT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Timing constants
CHECK_INTERVAL_SECONDS = 60  # Check every minute
SILENCE_THRESHOLD_MINUTES = 5  # Generate after 5 min of no events
MAX_WAIT_MINUTES = 30  # Generate after 30 min regardless
HISTORY_HOURS = 12  # Show last 12 hours in entity/prompt


@dataclass
class StoryData:
    """Data structure for story state."""

    # Transient (memory only)
    pending_events: list[dict[str, Any]] = field(default_factory=list)
    last_event_time: datetime | None = None
    last_generation_time: datetime | None = None

    # From database (last 12h)
    recent_story: str = ""
    story_entries: list[dict[str, Any]] = field(default_factory=list)


class StoryCoordinator(DataUpdateCoordinator):
    """Coordinator to manage story generation."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=CHECK_INTERVAL_SECONDS),
        )
        self.entry = entry
        self._db_path = Path(hass.config.path("ha_today.db"))
        self.data = StoryData()
        self._cancel_interval = None

    async def async_start(self) -> None:
        """Start the coordinator."""
        _LOGGER.info("Starting story coordinator...")

        # Initialize database
        await self._init_database()

        # Load recent story entries
        await self._load_recent_entries()

        # Set up check interval
        self._cancel_interval = async_track_time_interval(
            self.hass, self._check_and_generate, timedelta(seconds=CHECK_INTERVAL_SECONDS)
        )

        _LOGGER.info(
            "Story coordinator started - checking every %ds, silence threshold: %dm, max wait: %dm",
            CHECK_INTERVAL_SECONDS,
            SILENCE_THRESHOLD_MINUTES,
            MAX_WAIT_MINUTES,
        )

    async def async_stop(self) -> None:
        """Stop the coordinator."""
        if self._cancel_interval:
            self._cancel_interval()

    async def _init_database(self) -> None:
        """Initialize SQLite database."""
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS story_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    content TEXT NOT NULL
                )
            """)
            await db.commit()
        _LOGGER.debug("Database initialized at %s", self._db_path)

    async def _load_recent_entries(self) -> None:
        """Load story entries from last 12 hours."""
        cutoff = (dt_util.now() - timedelta(hours=HISTORY_HOURS)).isoformat()

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT timestamp, content FROM story_entries WHERE timestamp > ? ORDER BY timestamp ASC",
                (cutoff,)
            ) as cursor:
                rows = await cursor.fetchall()

        self.data.story_entries = [
            {"timestamp": row["timestamp"], "content": row["content"]}
            for row in rows
        ]
        self.data.recent_story = self._format_story_with_days(self.data.story_entries)

        _LOGGER.info("Loaded %d story entries from last %dh", len(self.data.story_entries), HISTORY_HOURS)

    def _format_story_with_days(self, entries: list[dict[str, Any]]) -> str:
        """Format story entries with newlines and day headings (reverse order, newest first)."""
        if not entries:
            return ""

        # Reverse entries - most recent first
        reversed_entries = list(reversed(entries))

        lines = []
        current_date = None

        for entry in reversed_entries:
            # Parse the timestamp
            ts = datetime.fromisoformat(entry["timestamp"])
            entry_date = ts.date()
            time_str = ts.strftime("%H:%M")

            # If we moved to a different (older) day, add heading for the day we just finished
            if current_date is not None and entry_date != current_date:
                lines.append(f"## {current_date.strftime('%A, %B %d')}")
                lines.append("")

            current_date = entry_date

            # Add entry - no timestamp if it starts with --- (horizontal rule segment)
            content = entry['content']
            if content.startswith("---"):
                lines.append(content)
            else:
                lines.append(f"**{time_str}** {content}")

        # Add heading for the oldest day at the bottom
        if current_date is not None:
            lines.append(f"## {current_date.strftime('%A, %B %d')}")

        return "\n".join(lines)

    async def manual_generate(self) -> None:
        """Manually trigger story generation."""
        _LOGGER.info("=== Manual generation triggered ===")
        await self._generate_segment()

    async def delete_last_entry(self) -> None:
        """Delete the most recent story entry."""
        if not self.data.story_entries:
            _LOGGER.warning("No entries to delete")
            return

        # Get the last entry
        last_entry = self.data.story_entries[-1]
        timestamp = last_entry["timestamp"]

        # Delete from database
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "DELETE FROM story_entries WHERE timestamp = ?",
                (timestamp,)
            )
            await db.commit()

        # Remove from local state
        self.data.story_entries.pop()
        self.data.recent_story = self._format_story_with_days(self.data.story_entries)

        _LOGGER.info("Deleted entry from %s", timestamp)

        # Notify listeners
        self.async_set_updated_data(self.data)

    async def add_event(self, event_data: dict[str, Any]) -> None:
        """Add an event to the pending buffer."""
        event = {
            "timestamp": dt_util.now(),
            "event": event_data.get("event", ""),
            "entity_id": event_data.get("entity_id"),
            "metadata": event_data.get("metadata", {}),
        }

        self.data.pending_events.append(event)
        self.data.last_event_time = event["timestamp"]

        _LOGGER.info(
            "Event added: '%s' (total pending: %d)",
            event["event"][:50],
            len(self.data.pending_events),
        )

        # Notify listeners that data has changed
        self.async_set_updated_data(self.data)

    async def _check_and_generate(self, *args) -> None:
        """Check if we should generate and do so if conditions met."""
        if not self.data.pending_events:
            return  # Nothing to process

        now = dt_util.now()

        # Calculate time since last event
        silence_duration = now - self.data.last_event_time if self.data.last_event_time else timedelta(hours=999)
        silence_met = silence_duration >= timedelta(minutes=SILENCE_THRESHOLD_MINUTES)

        # Calculate time since last generation
        if self.data.last_generation_time:
            wait_duration = now - self.data.last_generation_time
        else:
            # If never generated, use time since first event
            wait_duration = now - self.data.pending_events[0]["timestamp"]
        max_wait_met = wait_duration >= timedelta(minutes=MAX_WAIT_MINUTES)

        if silence_met or max_wait_met:
            reason = "silence" if silence_met else "max_wait"
            _LOGGER.info(
                "Generation triggered (%s) - %d events, silence: %.1fm, wait: %.1fm",
                reason,
                len(self.data.pending_events),
                silence_duration.total_seconds() / 60,
                wait_duration.total_seconds() / 60,
            )
            await self._generate_segment()

    async def _generate_segment(self) -> None:
        """Generate a story segment from pending events."""
        if not self.data.pending_events:
            _LOGGER.warning("No pending events to process")
            return

        try:
            # Build the prompt
            base_prompt = self.entry.data.get(CONF_BASE_PROMPT, DEFAULT_BASE_PROMPT)
            formatted_prompt = self._build_prompt(base_prompt)

            _LOGGER.info("Generating with %d events:", len(self.data.pending_events))
            for evt in self.data.pending_events:
                _LOGGER.info("  - %s: %s", evt["timestamp"].strftime("%H:%M:%S"), evt["event"])
            _LOGGER.info("=== PROMPT ===\n%s\n=== END PROMPT ===", formatted_prompt)

            # Call AI task service
            response = await self.hass.services.async_call(
                "ai_task",
                "generate_data",
                {
                    "task_name": "Home activity log",
                    "instructions": formatted_prompt,
                },
                blocking=True,
                return_response=True,
            )

            _LOGGER.info("=== AI RESPONSE ===\n%s\n=== END RESPONSE ===", response)

            # Extract segment from response
            segment = None
            if isinstance(response, dict):
                segment = response.get("data") or response.get("text")
            elif isinstance(response, str):
                segment = response

            if segment:
                segment = segment.strip()

            # Update generation time regardless of outcome
            self.data.last_generation_time = dt_util.now()

            # Check for NO_UPDATE response - keep events for next time
            # LLM might add explanation after NO_UPDATE, so check if it starts with it
            segment_check = segment.upper().split('\n')[0].strip() if segment else ""
            if not segment or segment_check in ("NO_UPDATE", "NO UPDATE", "NONE", "N/A") or segment_check.startswith("NO_UPDATE") or segment_check.startswith("NO UPDATE"):
                _LOGGER.info("LLM decided: no noteworthy events yet - keeping %d events for next check", len(self.data.pending_events))

                # Add a synthetic event so LLM knows how long since last generation
                skip_event = {
                    "timestamp": dt_util.now(),
                    "event": "[System: No story segment generated at this check]",
                    "entity_id": None,
                    "metadata": {"type": "system_skip"},
                }
                self.data.pending_events.append(skip_event)

                self.async_set_updated_data(self.data)
                return

            _LOGGER.info("Generated: '%s' (%d chars)", segment[:80], len(segment))

            # Save to database
            timestamp = dt_util.now().isoformat()
            async with aiosqlite.connect(self._db_path) as db:
                await db.execute(
                    "INSERT INTO story_entries (timestamp, content) VALUES (?, ?)",
                    (timestamp, segment)
                )
                await db.commit()

            # Update local state
            self.data.story_entries.append({"timestamp": timestamp, "content": segment})
            self.data.recent_story = self._format_story_with_days(self.data.story_entries)

            # Clear pending events
            self.data.pending_events.clear()

            _LOGGER.info("✓ Story entry saved to database")

            # Notify listeners
            self.async_set_updated_data(self.data)

        except Exception as err:
            _LOGGER.error("Failed to generate: %s", err, exc_info=True)

    def _build_prompt(self, base_prompt: str) -> str:
        """Build the LLM prompt from template."""
        # Get all areas in the home
        from homeassistant.helpers import area_registry
        area_reg = area_registry.async_get(self.hass)
        areas = [area.name for area in area_reg.async_list_areas()]
        areas_text = ", ".join(sorted(areas)) if areas else "Unknown"

        # Format pending events
        events_text = "\n".join(
            f"- {evt['timestamp'].strftime('%H:%M')}: {evt['event']}"
            for evt in self.data.pending_events
        )

        # Format recent story (last 12h)
        story_so_far = self.data.recent_story if self.data.recent_story else "No entries yet today."

        # Fill template
        return base_prompt.format(
            events=events_text,
            previous_segments=story_so_far,
            areas=areas_text,
        )
