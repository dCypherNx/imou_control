from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import HomeAssistant

from .const import DOMAIN


class ImouPresetText(TextEntity):
    def __init__(self, hass: HomeAssistant, device_id: str, data: dict):
        self._hass = hass
        self._device_id = device_id
        self._data = data
        self._attr_should_poll = False
        self._attr_mode = TextMode.TEXT
        self._attr_unique_id = f"{self._device_id}_preset_name"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, self._device_id)})
        self._attr_has_entity_name = True
        self._attr_translation_key = "preset_name"

    @property
    def native_value(self) -> str | None:
        return self._data.get("preset_name", "")

    async def async_set_value(self, value: str) -> None:
        self._data["preset_name"] = value
        self.async_write_ha_state()


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, dev in data["devices"].items():
        entities.append(ImouPresetText(hass, device_id, dev))
    async_add_entities(entities)
