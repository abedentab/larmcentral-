"""Editable select settings for Larmcentral."""

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_START_LEVEL, DOMAIN, LEVEL_RED, LEVEL_YELLOW


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([LarmStartLevelSelect(hass, entry)])


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
