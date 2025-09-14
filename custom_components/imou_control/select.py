# custom_components/imou_control/select.py
from __future__ import annotations
from typing import List
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import callback
from . import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    devices = data.get("devices", [])

    entities: List[ImouCameraPresetSelect] = []
    for d in devices:
        entities.append(ImouCameraPresetSelect(entry, d))
    async_add_entities(entities, True)

class ImouCameraPresetSelect(SelectEntity):
    _attr_icon = "mdi:format-list-numbered"

    def __init__(self, entry, device: dict):
        self._entry = entry
        self._device_id = device["device_id"]
        self._name = device.get("name") or "Imou Camera"
        self._model = device.get("model") or ""
        # valores iniciais (sem presets ainda)
        self._attr_name = f"Imou {self._name} Preset"
        self._attr_unique_id = f"{entry.entry_id}:{self._device_id}:preset_select"
        self._attr_options = ["0 — none"]
        self._attr_current_option = "0 — none"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, f"{self._entry.entry_id}:{self._device_id}")},
            name=f"Imou {self._name}",
            model=self._model or None,
            manufacturer="Imou",
        )

    async def async_select_option(self, option: str) -> None:
        # por enquanto, sem lógica de presets — isso entra na próxima etapa
        self._attr_current_option = option
        self.async_write_ha_state()
