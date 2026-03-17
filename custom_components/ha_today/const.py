"""Constants for the HA Today integration."""

DOMAIN = "ha_today"

# Services
SERVICE_COMMIT_EVENT = "commit_event"

# Config keys
CONF_AGENT_ID = "agent_id"
CONF_BASE_PROMPT = "base_prompt"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_UPDATE_INTERVAL = 60  # minutes
DEFAULT_BASE_PROMPT = """You are the storyteller of a home. Generate brief story segments from hourly events.

STYLE:
- Present tense, third person narrative
- Poetic but concise (2-4 sentences max)
- Under 200 characters for receipt printer
- Connect events into flowing narrative

EVENTS FROM LAST HOUR:
{events}

PREVIOUS SEGMENTS TODAY:
{previous_segments}

Generate next brief segment (2-4 sentences, <200 chars):"""

# Entity attributes
ATTR_STORY_TEXT = "story_text"
ATTR_SEGMENT_COUNT = "segment_count"
ATTR_EVENTS_COUNT = "events_count"
ATTR_LAST_SEGMENT = "last_segment"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "ha_today.story_data"
