# HA Today - Daily Home Story Generator

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/ameesme/ha-today.svg)](https://github.com/ameesme/ha-today/releases)
[![License](https://img.shields.io/github/license/ameesme/ha-today.svg)](LICENSE)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ameesme&repository=ha-today&category=integration)

Generate daily narrative stories from your home automation events using AI. Events are collected hourly, sent to your conversation agent (OpenAI, Claude, etc.), and compiled into brief story segments perfect for receipt printer output.

## Features

- **Event Collection**: `ha_today.commit_event` service for automations
- **Hourly AI Generation**: LLM-powered story segments every hour
- **Daily Rollover**: Stories archive at midnight, new day begins
- **Persistent Storage**: Survives restarts, zero data loss
- **Receipt Printer Ready**: Brief segments (<200 chars)
- **Configurable**: Choose AI agent, customize prompts, set intervals

## Installation

**HACS**: Click the badge above or add `https://github.com/ameesme/ha-today` as a custom repository.

**Manual**: Copy `custom_components/ha_today` to your Home Assistant config directory.

Restart Home Assistant after installation.

## Configuration

**Prerequisites**: A configured conversation agent (OpenAI, Claude, etc.)

1. Settings → Devices & Services → Add Integration → "HA Today"
2. Select conversation agent
3. Customize prompt (optional)
4. Set update interval (default: 60 minutes)

## Usage

### Commit Events

```yaml
service: ha_today.commit_event
data:
  event: "Living room motion detected"
  entity_id: binary_sensor.living_room_motion  # optional
  metadata:                                      # optional
    duration: 300
```

### Example Automations

```yaml
automation:
  - alias: "Story: Motion"
    trigger:
      platform: state
      entity_id: binary_sensor.living_room_motion
      to: "on"
    action:
      service: ha_today.commit_event
      data:
        event: "Movement in living room"
        entity_id: "{{ trigger.entity_id }}"

  - alias: "Story: Door"
    trigger:
      platform: state
      entity_id: binary_sensor.front_door
      to: "on"
    action:
      service: ha_today.commit_event
      data:
        event: "Front door opened"

  - alias: "Story: Temperature"
    trigger:
      platform: numeric_state
      entity_id: sensor.living_room_temperature
      above: 25
    action:
      service: ha_today.commit_event
      data:
        event: "Living room heated up to {{ states(trigger.entity_id) }}°C"
        metadata:
          temperature: "{{ states(trigger.entity_id) }}"
```

### Sensors

**`sensor.ha_today_story`**
- State: `"5 segments"` or `"No story yet"`
- Attributes: `story_text`, `segment_count`, `events_count`, `last_segment`

**`sensor.ha_today_yesterday`**
- State: `"Completed"` or `"No story yet"`
- Attributes: `story_text`

**`sensor.ha_today_last_updated`**
- State: ISO timestamp

### Display Story

```yaml
type: markdown
content: |
  ## Today's Story
  {{ state_attr('sensor.ha_today_story', 'story_text') }}

  **Segments**: {{ state_attr('sensor.ha_today_story', 'segment_count') }}
  **Pending**: {{ state_attr('sensor.ha_today_story', 'events_count') }}
```

### Print to Receipt Printer

```yaml
automation:
  - alias: "Print Story"
    trigger:
      platform: state
      entity_id: sensor.ha_today_story
      attribute: segment_count
    action:
      service: esphome.thermal_printer_print
      data:
        text: |
          === HOME STORY ===
          {{ now().strftime('%H:%M') }}

          {{ state_attr('sensor.ha_today_story', 'last_segment') }}

          ------------------
```

## How It Works

1. Automations call `ha_today.commit_event` throughout the day
2. Every hour, integration sends buffered events to your AI agent with prompt
3. Generated segment appends to today's story
4. At midnight, today → yesterday, new story begins
5. All data persists to `.storage/ha_today.story_data`

## Custom Prompts

The default prompt generates poetic narratives. Customize via Settings → HA Today → Configure.

**Template Variables:**
- `{events}`: Formatted event list with timestamps
- `{previous_segments}`: All segments generated today

**Example - Factual:**
```
Summarize these events factually:

{events}

Previous: {previous_segments}

Summary (1-2 sentences, <150 chars):
```

**Example - Detailed:**
```
Chronicle this smart home's life in detail.

Events: {events}
Story so far: {previous_segments}

Continue (3-5 sentences):
```

## Performance

- **API Calls**: One per update interval (default: 24/day)
- **Storage**: <1KB per day
- **Event Limit**: None (all events included in prompt)

## License

MIT License - See [LICENSE](LICENSE)
