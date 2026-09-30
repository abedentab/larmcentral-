"""Config flow for Larmcentral."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_ENABLED,
    CONF_ENTITY,
    CONF_NAME,
    CONF_NOTIFY_RED,
    CONF_RED_DELAY,
    CONF_START_LEVEL,
    CONF_TRIGGER_STATE,
    DEFAULT_ENABLED,
    DEFAULT_NOTIFY_RED,
    DEFAULT_RED_DELAY,
    DEFAULT_START_LEVEL,
    DEFAULT_TRIGGER_STATE,
    DOMAIN,
    LEVEL_RED,
    LEVEL_YELLOW,
)


class LarmcentralConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ENTITY])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): selector.TextSelector(),
                vol.Required(CONF_ENTITY): selector.EntitySelector(
                    selector.EntitySelectorConfig()
                ),
                vol.Required(
                    CONF_TRIGGER_STATE, default=DEFAULT_TRIGGER_STATE
                ): selector.TextSelector(),
                vol.Required(
                    CONF_START_LEVEL, default=DEFAULT_START_LEVEL
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": LEVEL_YELLOW, "label": "Gul"},
                            {"value": LEVEL_RED, "label": "Röd"},
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_RED_DELAY, default=DEFAULT_RED_DELAY
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0,
                        max=1440,
                        step=1,
                        unit_of_measurement="min",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Required(
                    CONF_ENABLED, default=DEFAULT_ENABLED
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_NOTIFY_RED, default=DEFAULT_NOTIFY_RED
                ): selector.BooleanSelector(),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
