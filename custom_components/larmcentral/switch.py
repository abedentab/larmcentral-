"""Editable switches for Larmcentral alarm configuration."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ENABLED, CONF_NOTIFY_RED, CONF_OBJECT, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([
        LarmEnabledSwitch(hass, entry),
        LarmNotifySwitch(hass, entry),
    ])


class _ConfigSwitch(SwitchEntity):
    _attr_has_entity_name = True

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, key: str, name: str, icon: str) -> None:
        self.hass = hass
        self.entry = entry
        self.key = key
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, "object", str(entry.data.get(CONF_OBJECT, entry.data["name"])).strip().casefold())},
            "name": str(entry.data.get(CONF_OBJECT, entry.data["name"])).strip(),
        }

    @property
    def is_on(self) -> bool:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]["runtime"]
        return bool(getattr(runtime.definition, self.key))

    async def _set(self, value: bool) -> None:
        runtime = self.hass.data[DOMAIN][self.entry.entry_id]["runtime"]
        setattr(runtime.definition, self.key, value)
        data = dict(self.entry.data)
        data[self.key] = value
        self.hass.config_entries.async_update_entry(self.entry, data=data)
        self.async_write_ha_state()
        refresh = self.hass.data[DOMAIN][self.entry.entry_id].get("refresh")
        if refresh:
            refresh()

    async def async_turn_on(self, **kwargs) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self._set(False)


class LarmEnabledSwitch(_ConfigSwitch):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, CONF_ENABLED, "Övervakning aktiv", "mdi:cctv")


class LarmNotifySwitch(_ConfigSwitch):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(hass, entry, CONF_NOTIFY_RED, "Mobilavisering vid rött", "mdi:bell")
