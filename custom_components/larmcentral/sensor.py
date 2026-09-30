"""Sensors exposing Larmcentral alarm state and history."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_NAME, DOMAIN

EVENT_ALARM_CHANGED = "larmcentral_alarm_changed"
HISTORY_KEY = "_history"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        [
            LarmcentralAlarmSensor(hass, entry),
            LarmcentralHistorySensor(hass, entry),
        ],
        True,
    )


class _EventSensor(SensorEntity):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._remove_event_listener = None

    async def async_added_to_hass(self) -> None:
        @callback
        def event_received(event: Event) -> None:
            self.async_write_ha_state()

        self._remove_event_listener = self.hass.bus.async_listen(
            EVENT_ALARM_CHANGED, event_received
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_event_listener is not None:
            self._remove_event_listener()
            self._remove_event_listener = None


class LarmcentralAlarmSensor(_EventSensor):
    _attr_has_entity_name = True
    _attr_name = "Larmstatus"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
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


class LarmcentralHistorySensor(_EventSensor):
    _attr_name = "Larmcentral historik"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry)
        self._attr_unique_id = "larmcentral_history"

    @property
    def native_value(self) -> int:
        history = self.hass.data[DOMAIN][HISTORY_KEY].as_list()
        return len(history)

    @property
    def extra_state_attributes(self) -> dict:
        history = self.hass.data[DOMAIN][HISTORY_KEY].as_list()
        return {
            "events": [
                {
                    "timestamp": item.timestamp.isoformat(),
                    "entity_id": item.entity_id,
                    "name": item.name,
                    "level": item.level,
                }
                for item in history
            ]
        }
