"""Config flow for HA Today integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_AGENT_ID,
    CONF_BASE_PROMPT,
    CONF_UPDATE_INTERVAL,
    DEFAULT_BASE_PROMPT,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _get_conversation_agents(hass: HomeAssistant) -> list[str]:
    """Get list of available conversation agents."""
    agents = []

    # Get conversation agents from the conversation integration
    if "conversation" in hass.config.components:
        try:
            # Try to get agents from conversation integration
            from homeassistant.components import conversation

            agent_info = await conversation.async_get_agent_info(hass, None)

            # Get all available agents
            if hasattr(conversation, "async_get_conversation_agents"):
                agent_ids = await conversation.async_get_conversation_agents(hass)
                agents.extend(agent_ids)
            else:
                # Fallback: use default agent
                agents.append("conversation.home_assistant")

        except Exception as err:
            _LOGGER.warning("Could not fetch conversation agents: %s", err)
            agents.append("conversation.home_assistant")
    else:
        agents.append("conversation.home_assistant")

    return agents if agents else ["conversation.home_assistant"]


class HAtodayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Today."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the input
            agent_id = user_input.get(CONF_AGENT_ID)
            update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

            # Check if agent exists
            agents = await _get_conversation_agents(self.hass)
            if agent_id not in agents:
                errors[CONF_AGENT_ID] = "invalid_agent"

            # Validate update interval
            if update_interval <= 0:
                errors[CONF_UPDATE_INTERVAL] = "invalid_interval"

            if not errors:
                # Create the entry
                return self.async_create_entry(
                    title="HA Today",
                    data=user_input,
                )

        # Get available conversation agents
        agents = await _get_conversation_agents(self.hass)

        # Build the configuration schema
        data_schema = vol.Schema(
            {
                vol.Required(CONF_AGENT_ID, default=agents[0] if agents else ""): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=agents,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_BASE_PROMPT, default=DEFAULT_BASE_PROMPT
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=1440,  # Max 24 hours
                        unit_of_measurement="minutes",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HAodayOptionsFlow:
        """Get the options flow for this handler."""
        return HAodayOptionsFlow(config_entry)


class HAodayOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for HA Today."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate the input
            agent_id = user_input.get(CONF_AGENT_ID)
            update_interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

            # Check if agent exists
            agents = await _get_conversation_agents(self.hass)
            if agent_id not in agents:
                errors[CONF_AGENT_ID] = "invalid_agent"

            # Validate update interval
            if update_interval <= 0:
                errors[CONF_UPDATE_INTERVAL] = "invalid_interval"

            if not errors:
                # Update the config entry data
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data={**self.config_entry.data, **user_input},
                )
                return self.async_create_entry(title="", data={})

        # Get available conversation agents
        agents = await _get_conversation_agents(self.hass)

        # Get current values
        current_agent = self.config_entry.data.get(CONF_AGENT_ID, agents[0] if agents else "")
        current_prompt = self.config_entry.data.get(CONF_BASE_PROMPT, DEFAULT_BASE_PROMPT)
        current_interval = self.config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

        # Build the options schema
        options_schema = vol.Schema(
            {
                vol.Required(CONF_AGENT_ID, default=current_agent): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=agents,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(CONF_BASE_PROMPT, default=current_prompt): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
                vol.Required(CONF_UPDATE_INTERVAL, default=current_interval): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=1440,
                        unit_of_measurement="minutes",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )
