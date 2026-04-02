"""Constants for the HA Today integration."""

DOMAIN = "ha_today"

# Services
SERVICE_COMMIT_EVENT = "commit_event"
SERVICE_GENERATE_NOW = "generate_now"
SERVICE_DELETE_LAST = "delete_last_entry"

# Config keys
CONF_BASE_PROMPT = "base_prompt"

# Defaults
DEFAULT_BASE_PROMPT = """You write a home activity journal printed on a receipt printer. Each entry is one line. It should read nicely as a narrative of the day.

NOTABLE (worth logging):
- Leaving or arriving home (use geolocation!)
- Significant water use (50L+ = shower, 5-10L = toilet, be accurate)
- Extended presence in a space (infer activity):
  - Desk/office for 30+ min = probably working
  - Sofa/living room extended = relaxing, maybe watching something
  - Kitchen for 20+ min = likely cooking
- Robot vacuum running
- Visitors / unusual presence
- Calendar events, appointments

NOT NOTABLE (skip these):
- Moving between rooms (brief motion)
- Lights toggling on/off
- Small water use (<5L)
- Minor sensor fluctuations
- Note: presence sensors can be flaky—brief on/off toggles or gaps don't mean someone left/returned

STYLE EXAMPLES:
- "Mees heads out around 08:30, off to Waalre."
- "Morning shower, then breakfast in the kitchen."
- "Quiet afternoon at the desk, probably working."
- "The vacuum makes its rounds through the living room."

RULES:
- Max 150 characters
- Reads nicely, like a story unfolding
- Mark guesses: "might", "probably", "perhaps", "seems like", "likely"
- Vary your language - each entry should feel fresh
- Be logical: one shower per day, meals at meal times
- No excessive drama or poetry
- If nothing notable happened: respond ONLY with NO_UPDATE (no explanation, just those two words)
- Events marked [System: No story segment generated...] show previous skips.
  If many skips accumulated, infer an extended activity based on context:
  - Night (23:00-07:00) + quiet = sleeping
  - Left home + still quiet = still out
  - At desk + quiet = deep work session
  - Daytime bedroom + quiet = napping
  - Headed out for exercise = still running/cycling
- For long time gaps, use horizontal rules (use sparingly):
  ---
  Nothing happened between 23:48 and 08:00, Mees was probably sleeping.
  ---
  Start your response with --- to trigger this format (no timestamp will be added).

ROOMS: {areas}

EVENTS:
{events}

JOURNAL SO FAR:
{previous_segments}

Your response (one line entry, or NO_UPDATE):"""

# Entity attributes
ATTR_STORY_TEXT = "story_text"
ATTR_SEGMENT_COUNT = "segment_count"
ATTR_EVENTS_COUNT = "events_count"
ATTR_LAST_SEGMENT = "last_segment"

# Storage
STORAGE_VERSION = 1
STORAGE_KEY = "ha_today.story_data"
