from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import HomeAssistant

from .const import DOMAIN


class ImouPresetSelect(SelectEntity):
    def __init__(self, hass: HomeAssistant, api, device_id: str, data: dict):
        self._hass = hass
        self._api = api
        self._device_id = device_id
        self._data = data
        self._attr_should_poll = False
        self._attr_options = list(data["presets"].keys())
        self._attr_unique_id = f"{self._device_id}_presets"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer="Imou",
            name=data["name"],
        )
        self._attr_has_entity_name = False
        self._attr_translation_key = "presets"

    @property
    def current_option(self) -> str | None:
        return self._data.get("last_preset")

    async def async_select_option(self, option: str) -> None:
        await self._hass.services.async_call(
            DOMAIN,
            "call_preset",
            {"device": self._device_id, "preset": option},
            context=self._context,
        )
        self._data["last_preset"] = option
        self.async_write_ha_state()

    def async_update_presets(self) -> None:
        self._attr_options = list(self._data["presets"].keys())
        self.async_write_ha_state()

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    entities = []
    for device_id, dev in data["devices"].items():
        ent = ImouPresetSelect(hass, api, device_id, dev)
        dev["select_entity"] = ent
        entities.append(ent)
    async_add_entities(entities)
