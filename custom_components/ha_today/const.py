"""Constants for the HA Today integration."""

DOMAIN = "ha_today"

# Services
SERVICE_COMMIT_EVENT = "commit_event"
SERVICE_GENERATE_NOW = "generate_now"

# Config keys
CONF_BASE_PROMPT = "base_prompt"

# Defaults
DEFAULT_BASE_PROMPT = """You maintain a home activity journal. Only log NOTABLE day events.

NOTABLE (worth logging):
- Taking a shower, water usage
- Leaving or arriving home
- Robot vacuum running
- Visitors / unusual presence
- Meal times, cooking
- Significant routines

NOT NOTABLE (skip these):
- Random motion detection
- Lights toggling on/off
- Walking around the house
- Minor sensor changes

STYLE (copy exactly):
- "Front door opens, Mees leaving? Heading to Waalre. Security on."
- "78 liters used at 08:15, morning shower. Kitchen lights on, breakfast."
- "Robot vacuum started in living room, cleaning day."

RULES:
- Max 150 chars
- Plain facts, subtle assumptions OK
- No poetry, no drama
- If nothing notable: respond with exactly NO_UPDATE

ROOMS: {areas}

EVENTS:
{events}

JOURNAL SO FAR:
{previous_segments}

Your response (entry or NO_UPDATE):"""

# Entity attributes
ATTR_STORY_TEXT = "story_text"
ATTR_SEGMENT_COUNT = "segment_count"
ATTR_EVENTS_COUNT = "events_count"
ATTR_LAST_SEGMENT = "last_segment"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "ha_today.story_data"
