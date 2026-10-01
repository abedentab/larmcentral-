"""Editable number settings for Larmcentral."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_OBJECT, CONF_RED_DELAY, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([LarmRedDelayNumber(hass, entry)])


class LarmRedDelayNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "🟥 Rött efter"
    _attr_icon = "mdi:timer-alert"
    _attr_native_min_value = 0
    _attr_native_max_value = 1440
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{CONF_RED_DELAY}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "object", str(entry.data.get(CONF_OBJECT, entry.data["name"])).strip().casefold())},
            "name": str(entry.data.get(CONF_OBJECT, entry.data["name"])).strip(),
        }

    @property
    def native_value(self) -> float:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]["runtime"]
        return float(runtime.definition.red_delay)

    async def async_set_native_value(self, value: float) -> None:
        minutes = int(value)
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]["runtime"]
        runtime.definition.red_delay = minutes
        data = dict(self.entry.data)
        data[CONF_RED_DELAY] = minutes
        self.hass.config_entries.async_update_entry(self.entry, data=data)
        self.async_write_ha_state()
        refresh = self.hass.data[DOMAIN][self.entry.entry_id].get("refresh")
        if refresh:
            refresh()
