"""Config flow for HA Today integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_BASE_PROMPT,
    DEFAULT_BASE_PROMPT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class HAtodayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Today."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title="HA Today",
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_BASE_PROMPT, default=DEFAULT_BASE_PROMPT
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> HAtodayOptionsFlow:
        """Get the options flow for this handler."""
        return HAtodayOptionsFlow()


class HAtodayOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for HA Today."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
            )
            return self.async_create_entry(title="", data={})

        current_prompt = self.config_entry.data.get(CONF_BASE_PROMPT, DEFAULT_BASE_PROMPT)

        options_schema = vol.Schema(
            {
                vol.Required(CONF_BASE_PROMPT, default=current_prompt): selector.TextSelector(
                    selector.TextSelectorConfig(
                        multiline=True,
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
