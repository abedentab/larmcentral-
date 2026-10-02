"""Config flow for Larmcentral."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    ALARM_TYPE_CUSTOM,
    ALARM_TYPE_IR,
    ALARM_TYPE_LEAK,
    ALARM_TYPE_LEVEL,
    ALARM_TYPE_MOTION,
    ALARM_TYPE_PING,
    ALARM_TYPE_SWITCH,
    ALARM_TYPE_TEMPERATURE,
    CONF_ALARM_TYPE,
    CONF_CUSTOM_ALARM_TYPE,
    CONF_ENABLED,
    CONF_ENTITY,
    CONF_NAME,
    CONF_NOTIFY_RED,
    CONF_OBJECT,
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

ALARM_TYPE_LABELS = {
    ALARM_TYPE_MOTION: "Rörelse",
    ALARM_TYPE_PING: "Ping",
    ALARM_TYPE_SWITCH: "Brytarlarm",
    ALARM_TYPE_IR: "IR",
    ALARM_TYPE_LEVEL: "Nivå",
    ALARM_TYPE_LEAK: "Läckage",
    ALARM_TYPE_TEMPERATURE: "Temperatur",
    ALARM_TYPE_CUSTOM: "Egen",
}


def _schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_OBJECT): selector.TextSelector(),
            vol.Required(CONF_ALARM_TYPE, default=ALARM_TYPE_MOTION): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        {"value": value, "label": label}
                        for value, label in ALARM_TYPE_LABELS.items()
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional(CONF_CUSTOM_ALARM_TYPE): selector.TextSelector(),
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


class LarmcentralConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    @staticmethod
    def async_get_options_flow(config_entry):
        return LarmcentralOptionsFlow(config_entry)

    async def async_migrate_entry(self, hass, config_entry):
        """Migrate older Larmcentral entries to version 2."""
        if config_entry.version > self.VERSION:
            return False

        if config_entry.version == 1:
            data = dict(config_entry.data)

            # Older alarms did not have object/alarm-type metadata.
            # Preserve their working runtime settings and add safe defaults.
            old_name = str(data.get(CONF_NAME, config_entry.title or "")).strip()
            data.setdefault(CONF_OBJECT, old_name or "Larm")
            data.setdefault(CONF_ALARM_TYPE, ALARM_TYPE_CUSTOM)
            data.setdefault(CONF_CUSTOM_ALARM_TYPE, old_name or "Larm")

            hass.config_entries.async_update_entry(
                config_entry,
                data=data,
                version=2,
            )

        return True

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            object_name = user_input[CONF_OBJECT].strip()
            alarm_type = user_input[CONF_ALARM_TYPE]
            custom_type = user_input.get(CONF_CUSTOM_ALARM_TYPE, "").strip()

            if alarm_type == ALARM_TYPE_CUSTOM and not custom_type:
                errors[CONF_CUSTOM_ALARM_TYPE] = "custom_alarm_type_required"
            else:
                alarm_type_name = (
                    custom_type
                    if alarm_type == ALARM_TYPE_CUSTOM
                    else ALARM_TYPE_LABELS[alarm_type]
                )

                data = dict(user_input)
                data[CONF_OBJECT] = object_name
                data[CONF_CUSTOM_ALARM_TYPE] = custom_type
                data[CONF_NAME] = f"{object_name} – {alarm_type_name}"

                await self.async_set_unique_id(data[CONF_ENTITY])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=data[CONF_NAME],
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(),
            errors=errors,
        )


class LarmcentralOptionsFlow(config_entries.OptionsFlow):
    """Edit an existing Larmcentral alarm."""

    async def async_step_init(self, user_input=None):
        errors = {}
        current = dict(self.config_entry.data)

        if user_input is not None:
            object_name = user_input[CONF_OBJECT].strip()
            alarm_type = user_input[CONF_ALARM_TYPE]
            custom_type = user_input.get(CONF_CUSTOM_ALARM_TYPE, "").strip()

            if alarm_type == ALARM_TYPE_CUSTOM and not custom_type:
                errors[CONF_CUSTOM_ALARM_TYPE] = "custom_alarm_type_required"
            else:
                alarm_type_name = (
                    custom_type
                    if alarm_type == ALARM_TYPE_CUSTOM
                    else ALARM_TYPE_LABELS[alarm_type]
                )
                data = dict(current)
                data.update(user_input)
                data[CONF_OBJECT] = object_name
                data[CONF_CUSTOM_ALARM_TYPE] = custom_type
                data[CONF_NAME] = f"{object_name} – {alarm_type_name}"

                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    data=data,
                    title=data[CONF_NAME],
                )
                return self.async_create_entry(title="", data={})

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_OBJECT,
                    default=current.get(CONF_OBJECT, ""),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_ALARM_TYPE,
                    default=current.get(CONF_ALARM_TYPE, ALARM_TYPE_MOTION),
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            {"value": value, "label": label}
                            for value, label in ALARM_TYPE_LABELS.items()
                        ],
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Optional(
                    CONF_CUSTOM_ALARM_TYPE,
                    default=current.get(CONF_CUSTOM_ALARM_TYPE, ""),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_TRIGGER_STATE,
                    default=current.get(CONF_TRIGGER_STATE, DEFAULT_TRIGGER_STATE),
                ): selector.TextSelector(),
                vol.Required(
                    CONF_START_LEVEL,
                    default=current.get(CONF_START_LEVEL, DEFAULT_START_LEVEL),
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
                    CONF_RED_DELAY,
                    default=current.get(CONF_RED_DELAY, DEFAULT_RED_DELAY),
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
                    CONF_ENABLED,
                    default=current.get(CONF_ENABLED, DEFAULT_ENABLED),
                ): selector.BooleanSelector(),
                vol.Required(
                    CONF_NOTIFY_RED,
                    default=current.get(CONF_NOTIFY_RED, DEFAULT_NOTIFY_RED),
                ): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
