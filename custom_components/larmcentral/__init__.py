"""Larmcentral custom integration."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .alarm import AlarmDefinition, AlarmRuntime
from .const import (
    CONF_ENABLED, CONF_ENTITY, CONF_NAME, CONF_NOTIFY_RED, CONF_RED_DELAY,
    CONF_START_LEVEL, CONF_TRIGGER_STATE, DEFAULT_ENABLED, DEFAULT_NOTIFY_RED,
    DEFAULT_RED_DELAY, DEFAULT_START_LEVEL, DEFAULT_TRIGGER_STATE, DOMAIN,
)
from .history import AlarmHistory, HistoryItem

EVENT_ALARM_CHANGED = "larmcentral_alarm_changed"
PLATFORMS = ["sensor"]
HISTORY_KEY = "_history"

WARNING_HELPER = "input_text.larm_varningar"
CRITICAL_HELPER = "input_text.larm_kritiska"
HISTORY_ENTITY = "input_button.larmhistorik"


def _remove_alarm(text: str, name: str) -> str:
    if text in ("unknown", "unavailable"):
        return ""
    return "\\n".join(
        line for line in text.split("\\n") if name not in line
    )


def _add_alarm(text: str, line: str, name: str) -> str:
    cleaned = _remove_alarm(text, name)
    return f"{cleaned}\\n{line}" if cleaned else line


async def _set_helper(hass: HomeAssistant, entity_id: str, value: str) -> None:
    if hass.states.get(entity_id) is None:
        return
    await hass.services.async_call(
        "input_text",
        "set_value",
        {"entity_id": entity_id, "value": value},
        blocking=True,
    )


async def _sync_dashboard(
    hass: HomeAssistant,
    definition: AlarmDefinition,
    level: str,
) -> None:
    """Mirror an alarm directly into the existing Larmcentral dashboard helpers."""
    name = definition.name
    warning_state = hass.states.get(WARNING_HELPER)
    critical_state = hass.states.get(CRITICAL_HELPER)

    warning_text = warning_state.state if warning_state else ""
    critical_text = critical_state.state if critical_state else ""

    if level == "yellow":
        await _set_helper(
            hass,
            CRITICAL_HELPER,
            _remove_alarm(critical_text, name),
        )
        await _set_helper(
            hass,
            WARNING_HELPER,
            _add_alarm(
                warning_text,
                f"{datetime.now().astimezone().strftime('%H:%M')} 🟨 {name}",
                name,
            ),
        )
        history_message = f"🟨 {name}"

    elif level == "red":
        await _set_helper(
            hass,
            WARNING_HELPER,
            _remove_alarm(warning_text, name),
        )
        await _set_helper(
            hass,
            CRITICAL_HELPER,
            _add_alarm(
                critical_text,
                f"{datetime.now().astimezone().strftime('%H:%M')} 🟥 {name}",
                name,
            ),
        )
        history_message = f"🟥 {name}"

    else:
        await _set_helper(
            hass,
            WARNING_HELPER,
            _remove_alarm(warning_text, name),
        )
        await _set_helper(
            hass,
            CRITICAL_HELPER,
            _remove_alarm(critical_text, name),
        )
        history_message = f"🟩 {name} återställt"

    if hass.states.get(HISTORY_ENTITY) is not None:
        await hass.services.async_call(
            "logbook",
            "log",
            {
                "name": "Larmhistorik",
                "message": history_message,
                "entity_id": HISTORY_ENTITY,
            },
            blocking=False,
        )


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
    hass.data[DOMAIN].setdefault(HISTORY_KEY, AlarmHistory())
    cancel_red_timer = None

    @callback
    def fire_change(previous_level: str | None, level: str | None) -> None:
        now = datetime.now().astimezone()
        normalized_level = level or "clear"

        hass.data[DOMAIN][HISTORY_KEY].add(
            HistoryItem(
                timestamp=now,
                entity_id=definition.entity,
                name=definition.name,
                level=normalized_level,
            )
        )

        hass.bus.async_fire(
            EVENT_ALARM_CHANGED,
            {
                "entry_id": entry.entry_id,
                "entity_id": definition.entity,
                "name": definition.name,
                "level": normalized_level,
                "previous_level": previous_level or "clear",
                "notify_red": definition.notify_red,
                "timestamp": now.isoformat(),
            },
        )

        hass.async_create_task(
            _sync_dashboard(hass, definition, normalized_level)
        )

        if normalized_level == "red" and definition.notify_red:
            hass.async_create_task(
                hass.services.async_call(
                    "notify",
                    "mobile_app_sm_a566b",
                    {
                        "title": "🟥 Larmcentral",
                        "message": f"{definition.name} är rött larm.",
                    },
                    blocking=False,
                )
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
