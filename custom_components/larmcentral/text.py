"""Editable text settings for Larmcentral."""

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_CUSTOM_ALARM_TYPE,
    CONF_OBJECT,
    CONF_TRIGGER_STATE,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([
        LarmObjectText(hass, entry),
        LarmTriggerStateText(hass, entry),
        LarmCustomAlarmTypeText(hass, entry),
    ])


class _ConfigText(TextEntity):
    _attr_has_entity_name = True
    _attr_mode = TextMode.TEXT
    _attr_native_min = 0
    _attr_native_max = 255

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        key: str,
        name: str,
        icon: str,
    ) -> None:
        self.hass = hass
        self.entry = entry
        self.key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data["name"],
        }

    @property
    def native_value(self) -> str:
        return str(self.entry.data.get(self.key, ""))

    async def async_set_value(self, value: str) -> None:
        data = dict(self.entry.data)
        data[self.key] = value.strip()
        self.hass.config_entries.async_update_entry(self.entry, data=data)
        self.async_write_ha_state()


class LarmObjectText(_ConfigText):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, CONF_OBJECT, "Objekt", "mdi:cube-outline")


class LarmTriggerStateText(_ConfigText):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            entry,
            CONF_TRIGGER_STATE,
            "Larm när tillståndet är",
            "mdi:state-machine",
        )

    async def async_set_value(self, value: str) -> None:
        value = value.strip()
        data = dict(self.entry.data)
        data[CONF_TRIGGER_STATE] = value
        self.hass.config_entries.async_update_entry(self.entry, data=data)
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]["runtime"]
        runtime.definition.trigger_state = value
        self.async_write_ha_state()
        refresh = self.hass.data[DOMAIN][self.entry.entry_id].get("refresh")
        if refresh:
            refresh()


class LarmCustomAlarmTypeText(_ConfigText):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            entry,
            CONF_CUSTOM_ALARM_TYPE,
            "Egen larmtyp",
            "mdi:pencil-outline",
        )
