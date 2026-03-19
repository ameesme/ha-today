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
DEFAULT_BASE_PROMPT = """You write a home activity log. Plain facts only, like a journal entry.

GOOD (copy this style exactly):
- "Front door opens, Mees leaving? Heading to Waalre. Security on, heat off."
- "Motion in hallway at 08:11, perhaps out of bed. 78 liters used, quick shower."
- "Two in studio, guests? Probably working."

BAD (never write like this):
- "Presence stirs through rooms" - too poetic
- "Dust motes drift" - too dramatic
- "soft hum of appliances" - unnecessary filler
- "weight of an empty room" - pretentious

RULES:
- Under 150 chars
- Plain language only
- No poetry, no metaphors, no drama
- Just state what happened

ROOMS: {areas}

EVENTS: {events}

PREVIOUS: {previous_segments}

Log entry:"""

# Entity attributes
ATTR_STORY_TEXT = "story_text"
ATTR_SEGMENT_COUNT = "segment_count"
ATTR_EVENTS_COUNT = "events_count"
ATTR_LAST_SEGMENT = "last_segment"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "ha_today.story_data"
