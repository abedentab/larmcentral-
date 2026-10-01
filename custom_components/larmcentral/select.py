"""Editable select settings for Larmcentral."""

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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
    CONF_START_LEVEL,
    DOMAIN,
    LEVEL_RED,
    LEVEL_YELLOW,
)

ALARM_TYPES = [
    ALARM_TYPE_MOTION,
    ALARM_TYPE_PING,
    ALARM_TYPE_SWITCH,
    ALARM_TYPE_IR,
    ALARM_TYPE_LEVEL,
    ALARM_TYPE_LEAK,
    ALARM_TYPE_TEMPERATURE,
    ALARM_TYPE_CUSTOM,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([
        LarmStartLevelSelect(hass, entry),
        LarmAlarmTypeSelect(hass, entry),
    ])


class LarmStartLevelSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Startnivå"
    _attr_icon = "mdi:alert"
    _attr_options = [LEVEL_YELLOW, LEVEL_RED]

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{CONF_START_LEVEL}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data["name"],
        }

    @property
    def current_option(self) -> str:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]["runtime"]
        return runtime.definition.start_level

    async def async_select_option(self, option: str) -> None:
        if option not in self.options:
            return
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]["runtime"]
        runtime.definition.start_level = option
        data = dict(self.entry.data)
        data[CONF_START_LEVEL] = option
        self.hass.config_entries.async_update_entry(self.entry, data=data)
        self.async_write_ha_state()
        refresh = self.hass.data[DOMAIN][self.entry.entry_id].get("refresh")
        if refresh:
            refresh()


class LarmAlarmTypeSelect(SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Larmtyp"
    _attr_icon = "mdi:alarm-light-outline"
    _attr_options = ALARM_TYPES

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{CONF_ALARM_TYPE}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data["name"],
        }

    @property
    def current_option(self) -> str:
        return self.entry.data.get(CONF_ALARM_TYPE, ALARM_TYPE_CUSTOM)

    async def async_select_option(self, option: str) -> None:
        if option not in self.options:
            return
        data = dict(self.entry.data)
        data[CONF_ALARM_TYPE] = option
        self.hass.config_entries.async_update_entry(self.entry, data=data)
        self.async_write_ha_state()
