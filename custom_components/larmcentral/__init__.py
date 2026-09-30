"""Larmcentral custom integration."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
)

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
    cancel_red_timer = None

    @callback
    def fire_change(previous_level: str | None, level: str | None) -> None:
        hass.bus.async_fire(
            EVENT_ALARM_CHANGED,
            {
                "entry_id": entry.entry_id,
                "entity_id": definition.entity,
                "name": definition.name,
                "level": level or "clear",
                "previous_level": previous_level or "clear",
                "notify_red": definition.notify_red,
                "timestamp": datetime.now().astimezone().isoformat(),
            },
        )

    @callback
    def schedule_red_timer() -> None:
        nonlocal cancel_red_timer
        if cancel_red_timer is not None:
            cancel_red_timer()
            cancel_red_timer = None

        if (
            runtime.level == "yellow"
            and definition.start_level == "yellow"
            and definition.red_delay > 0
            and runtime.active_since is not None
        ):
            due = runtime.active_since + timedelta(minutes=definition.red_delay)
            seconds = max(0, (due - datetime.now().astimezone()).total_seconds())

            @callback
            def turn_red(_now) -> None:
                nonlocal cancel_red_timer
                cancel_red_timer = None
                state = hass.states.get(definition.entity)
                if (
                    state is not None
                    and state.state == definition.trigger_state
                    and runtime.level == "yellow"
                ):
                    previous = runtime.level
                    runtime.level = "red"
                    fire_change(previous, "red")

            cancel_red_timer = async_call_later(hass, seconds, turn_red)

    @callback
    def publish(state: State | None) -> None:
        nonlocal cancel_red_timer
        previous_level = runtime.level
        state_value = state.state if state is not None else "unavailable"
        level = runtime.update(state_value, datetime.now().astimezone())

        if level is None and cancel_red_timer is not None:
            cancel_red_timer()
            cancel_red_timer = None

        if level != previous_level:
            fire_change(previous_level, level)

        if level == "yellow":
            schedule_red_timer()

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
        "cancel_red_timer": lambda: cancel_red_timer() if cancel_red_timer else None,
    }

    publish(hass.states.get(definition.entity))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        stored = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
        if stored:
            if stored.get("remove_listener"):
                stored["remove_listener"]()
            if stored.get("cancel_red_timer"):
                stored["cancel_red_timer"]()
    return unload_ok
