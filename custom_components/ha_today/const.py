"""Constants for the HA Today integration."""

DOMAIN = "ha_today"

# Services
SERVICE_COMMIT_EVENT = "commit_event"

# Config keys
CONF_BASE_PROMPT = "base_prompt"
CONF_UPDATE_INTERVAL = "update_interval"

# Defaults
DEFAULT_UPDATE_INTERVAL = 60  # minutes
DEFAULT_BASE_PROMPT = """You are the storyteller of a home. Generate the next brief segment to continue the story.

STYLE:
- Present tense, third person narrative
- Poetic but concise (2-4 sentences max)
- Under 200 characters for receipt printer
- Connect events into flowing narrative
- MUST end with a period (.)

EVENTS FROM LAST HOUR:
{events}

STORY SO FAR TODAY:
{previous_segments}

IMPORTANT: Return ONLY the next segment to add to the story. Do NOT repeat the previous story. Just write 2-4 sentences that continue from where it left off. End with a period."""

# Entity attributes
ATTR_STORY_TEXT = "story_text"
ATTR_SEGMENT_COUNT = "segment_count"
ATTR_EVENTS_COUNT = "events_count"
ATTR_LAST_SEGMENT = "last_segment"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "ha_today.story_data"
