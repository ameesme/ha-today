# HA Today - Daily Home Story Generator

A Home Assistant custom integration that generates a daily narrative story about your home by collecting events throughout the day and using an LLM to create story segments hourly.

## Features

- 📝 **Event Collection**: Service for automations to commit events throughout the day
- 🤖 **AI-Powered Stories**: Uses your configured conversation agent (OpenAI, Claude, etc.) to generate narrative segments
- ⏰ **Hourly Updates**: Collects events each hour and generates a new story segment
- 🌅 **Daily Rollover**: At midnight, today's story moves to yesterday and a new story begins
- 💾 **Data Persistence**: Stories and pending events survive Home Assistant restarts
- 🖨️ **Receipt Printer Friendly**: Segments kept brief (<200 chars) for thermal printer output
- ⚙️ **Configurable**: Choose your AI agent, customize the prompt, and set update intervals

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add this repository URL and select "Integration" as the category
5. Click "Install" on the HA Today card
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/ha_today` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

### Prerequisites

Before setting up HA Today, you need:
- A configured conversation agent (OpenAI, Anthropic Claude, etc.)
- The conversation integration enabled in Home Assistant

### Setup

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "HA Today"
4. Select your conversation agent from the dropdown
5. Customize the base prompt (or use the default)
6. Set the update interval in minutes (default: 60)
7. Click **Submit**

### Configuration Options

You can reconfigure the integration at any time:

1. Go to **Settings** → **Devices & Services**
2. Find the "HA Today" integration
3. Click **Configure**
4. Update your settings

## Usage

### Committing Events

Use the `ha_today.commit_event` service to add events to your story:

```yaml
service: ha_today.commit_event
data:
  event: "Living room motion detected"
  entity_id: binary_sensor.living_room_motion
  metadata:
    duration: 300
```

#### Service Parameters

- **event** (required): Description of what happened
- **entity_id** (optional): Related entity ID
- **metadata** (optional): Additional context as a dictionary

### Example Automations

**Track Motion Events:**
```yaml
automation:
  - alias: "Story: Motion Events"
    trigger:
      - platform: state
        entity_id: binary_sensor.living_room_motion
        to: "on"
    action:
      - service: ha_today.commit_event
        data:
          event: "Movement detected in living room"
          entity_id: "{{ trigger.entity_id }}"
```

**Track Door Opening:**
```yaml
automation:
  - alias: "Story: Front Door"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door
        to: "on"
    action:
      - service: ha_today.commit_event
        data:
          event: "Front door opened"
          entity_id: "{{ trigger.entity_id }}"
```

**Track Temperature Changes:**
```yaml
automation:
  - alias: "Story: Temperature Events"
    trigger:
      - platform: numeric_state
        entity_id: sensor.living_room_temperature
        above: 25
    action:
      - service: ha_today.commit_event
        data:
          event: "Living room temperature rose above 25°C"
          entity_id: "{{ trigger.entity_id }}"
          metadata:
            temperature: "{{ states(trigger.entity_id) }}"
```

### Accessing Stories

The integration creates three sensors:

#### 1. **Today's Story** (`sensor.ha_today_story`)
- **State**: Number of segments generated (e.g., "5 segments") or "No story yet"
- **Attributes**:
  - `story_text`: Full story text
  - `segment_count`: Number of segments
  - `events_count`: Pending events not yet processed
  - `last_segment`: Most recent segment text

#### 2. **Yesterday's Story** (`sensor.ha_today_yesterday`)
- **State**: "Completed" or "No story yet"
- **Attributes**:
  - `story_text`: Full yesterday's story

#### 3. **Last Updated** (`sensor.ha_today_last_updated`)
- **State**: Timestamp of last update (ISO format)
- **Device Class**: Timestamp

### Displaying Stories

**Template for Lovelace Card:**
```yaml
type: markdown
content: |
  ## Today's Story
  {{ state_attr('sensor.ha_today_story', 'story_text') }}

  ---

  **Segments**: {{ state_attr('sensor.ha_today_story', 'segment_count') }}
  **Pending Events**: {{ state_attr('sensor.ha_today_story', 'events_count') }}
```

**Access in Templates:**
```yaml
# Get today's full story
{{ state_attr('sensor.ha_today_story', 'story_text') }}

# Get yesterday's story
{{ state_attr('sensor.ha_today_yesterday', 'story_text') }}

# Get last segment
{{ state_attr('sensor.ha_today_story', 'last_segment') }}

# Get pending event count
{{ state_attr('sensor.ha_today_story', 'events_count') }}
```

### Print to Receipt Printer

If you have a thermal printer (like ESC/POS receipt printer), you can print story segments:

```yaml
automation:
  - alias: "Print Story Segment"
    trigger:
      - platform: state
        entity_id: sensor.ha_today_story
        attribute: segment_count
    action:
      - service: esphome.thermal_printer_print
        data:
          text: |
            === HOME STORY ===
            {{ now().strftime('%H:%M') }}

            {{ state_attr('sensor.ha_today_story', 'last_segment') }}

            ------------------
```

## How It Works

1. **Event Collection**: Throughout the day, your automations call `ha_today.commit_event` to record events
2. **Hourly Generation**: Every hour (or your configured interval), the integration:
   - Gathers all pending events from the last hour
   - Formats them with the base prompt
   - Sends to your conversation agent
   - Appends the generated segment to today's story
3. **Midnight Rollover**: At 00:00, today's story is saved as yesterday's story, and a fresh story begins
4. **Persistence**: All data (stories, events, segments) is saved to disk and survives restarts

## Customizing the Prompt

The default prompt generates poetic, concise narratives. You can customize it to change the style:

**Example: Minimalist Style**
```
Generate a brief factual summary of the following events:

{events}

Previous summaries: {previous_segments}

New summary (1-2 sentences, <150 chars):
```

**Example: Detailed Chronicle**
```
You are chronicling a smart home's daily life. Write a detailed narrative segment.

Events this hour:
{events}

Story so far:
{previous_segments}

Continue the chronicle (3-5 sentences):
```

**Template Variables:**
- `{events}`: Formatted list of events from the last hour
- `{previous_segments}`: All segments generated so far today

## Troubleshooting

### No Story Generated

**Check:**
1. Have you committed any events using `ha_today.commit_event`?
2. Is your conversation agent properly configured?
3. Check Home Assistant logs for errors: Settings → System → Logs

### Events Not Appearing

**Verify:**
1. Service calls are successful (check automation traces)
2. Events appear in pending count: `{{ state_attr('sensor.ha_today_story', 'events_count') }}`
3. Wait for the next update interval

### Integration Not Loading

**Common issues:**
1. Conversation integration not set up
2. No conversation agents configured
3. Check logs for specific error messages

### Stories Lost After Restart

Stories should persist automatically. If not:
1. Check `.storage/ha_today.story_data` file exists
2. Verify file permissions
3. Check logs for storage errors

## Performance Notes

- **No Event Limit**: The integration doesn't limit events per hour. If you have many events, consider:
  - Increasing update interval to reduce API calls
  - Filtering which events to commit
  - Using a more capable/expensive LLM model
- **API Costs**: Each segment generation makes one API call to your conversation agent
- **Storage**: Stories are text-only and use minimal disk space

## Future Enhancements

Potential features for future versions:
- Story export to file/notification
- Multiple story themes
- Event aggregation with cheaper models
- Per-room or per-person stories
- Weekly/monthly summaries
- Image attachment support

## Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check Home Assistant logs for detailed error messages
- Enable debug logging:
  ```yaml
  logger:
    default: info
    logs:
      custom_components.ha_today: debug
  ```

## License

MIT License - See LICENSE file for details

## Credits

Created for Home Assistant users who want a narrative summary of their home's daily activities.
