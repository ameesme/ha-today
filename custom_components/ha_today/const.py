"""Constants for the HA Today integration."""

DOMAIN = "ha_today"

# Services
SERVICE_COMMIT_EVENT = "commit_event"
SERVICE_GENERATE_NOW = "generate_now"

# Config keys
CONF_BASE_PROMPT = "base_prompt"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_UPDATE_INTERVAL = 60  # minutes
DEFAULT_BASE_PROMPT = """Summarize what happened in the home. Be factual with subtle assumptions about daily life.

STYLE EXAMPLES:
- "The front door opens, is Mees leaving? It appears so, heading to Waalre. Security on, heat off, lights off."
- "Motion in hallway at 08:11, perhaps someone got out of bed. 78 liters used, a reasonable shower."
- "Two people detected in studio, guests? They remain throughout the hour, probably working."

RULES:
- Max 200 characters
- Factual with subtle assumptions
- Brief rhetorical questions OK
- No drama or poetry

EVENTS:
{events}

STORY SO FAR:
{previous_segments}

Write the next short segment:"""

# Entity attributes
ATTR_STORY_TEXT = "story_text"
ATTR_SEGMENT_COUNT = "segment_count"
ATTR_EVENTS_COUNT = "events_count"
ATTR_LAST_SEGMENT = "last_segment"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "ha_today.story_data"
