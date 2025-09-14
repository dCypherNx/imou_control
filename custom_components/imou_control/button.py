from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import HomeAssistant

from .const import DOMAIN


class ImouMoveButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, api, device_id: str, data: dict):
        self._hass = hass
        self._api = api
        self._device_id = device_id
        self._data = data
        self._attr_should_poll = False

    @property
    def name(self) -> str:
        return f"{self._data['name']} Move"

    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_move"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._device_id)})

    async def async_press(self) -> None:
        h = self._data["coords"]["h"]
        v = self._data["coords"]["v"]
        z = self._data["coords"].get("z", 0.0)
        await self._hass.async_add_executor_job(
            self._api.set_position, self._device_id, h, v, z
        )


class ImouSavePresetButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, device_id: str, data: dict):
        self._hass = hass
        self._device_id = device_id
        self._data = data
        self._attr_should_poll = False

    @property
    def name(self) -> str:
        return f"{self._data['name']} Save Preset"

    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_save_preset"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._device_id)})

    async def async_press(self) -> None:
        preset = self._data.get("preset_name")
        if not preset:
            return
        await self._hass.services.async_call(
            DOMAIN,
            "save_preset",
            {"device": self._device_id, "preset": preset},
            blocking=True,
            context=self._context,
        )

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    api = data["api"]
    entities = []
    for device_id, dev in data["devices"].items():
        entities.append(ImouMoveButton(hass, api, device_id, dev))
        entities.append(ImouSavePresetButton(hass, device_id, dev))
    async_add_entities(entities)
