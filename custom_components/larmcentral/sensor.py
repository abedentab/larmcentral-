"""Sensors exposing the current Larmcentral state."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NAME, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([LarmcentralAlarmSensor(hass, entry)], True)


class LarmcentralAlarmSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Larmstatus"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_alarm"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.data[CONF_NAME],
        }

    @property
    def native_value(self) -> str:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]["runtime"]
        return runtime.level or "clear"

    @property
    def extra_state_attributes(self) -> dict:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]["runtime"]
        definition = runtime.definition
        return {
            "entity_id": definition.entity,
            "alarm_name": definition.name,
            "active_since": runtime.active_since.isoformat() if runtime.active_since else None,
            "start_level": definition.start_level,
            "red_delay": definition.red_delay,
            "notify_red": definition.notify_red,
        }
