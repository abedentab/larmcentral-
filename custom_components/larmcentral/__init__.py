"""Larmcentral custom integration."""

from __future__ import annotations

from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.event import async_track_state_change_event

from .alarm import AlarmDefinition, AlarmRuntime
from .const import (
    CONF_ENABLED, CONF_ENTITY, CONF_NAME, CONF_NOTIFY_RED, CONF_RED_DELAY,
    CONF_START_LEVEL, CONF_TRIGGER_STATE, DEFAULT_ENABLED, DEFAULT_NOTIFY_RED,
    DEFAULT_RED_DELAY, DEFAULT_START_LEVEL, DEFAULT_TRIGGER_STATE, DOMAIN,
)

EVENT_ALARM_CHANGED = "larmcentral_alarm_changed"
PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = entry.data
    definition = AlarmDefinition(
        entity=data[CONF_ENTITY],
        name=data[CONF_NAME],
        trigger_state=data.get(CONF_TRIGGER_STATE, DEFAULT_TRIGGER_STATE),
        start_level=data.get(CONF_START_LEVEL, DEFAULT_START_LEVEL),
        red_delay=int(data.get(CONF_RED_DELAY, DEFAULT_RED_DELAY)),
        enabled=data.get(CONF_ENABLED, DEFAULT_ENABLED),
        notify_red=data.get(CONF_NOTIFY_RED, DEFAULT_NOTIFY_RED),
    )
    runtime = AlarmRuntime(definition=definition)
    hass.data.setdefault(DOMAIN, {})

    @callback
    def publish(state: State | None) -> None:
        state_value = state.state if state is not None else "unavailable"
        previous_level = runtime.level
        level = runtime.update(state_value, datetime.now().astimezone())
        if level == previous_level:
            return
        hass.bus.async_fire(EVENT_ALARM_CHANGED, {
            "entry_id": entry.entry_id,
            "entity_id": definition.entity,
            "name": definition.name,
            "level": level or "clear",
            "previous_level": previous_level or "clear",
            "notify_red": definition.notify_red,
        })

    @callback
    def state_changed(event: Event) -> None:
        publish(event.data.get("new_state"))

    remove_listener = async_track_state_change_event(
        hass, [definition.entity], state_changed
    )
    hass.data[DOMAIN][entry.entry_id] = {
        "entry": entry,
        "runtime": runtime,
        "remove_listener": remove_listener,
    }
    publish(hass.states.get(definition.entity))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        stored = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if stored and stored.get("remove_listener"):
            stored["remove_listener"]()
    return unload_ok
