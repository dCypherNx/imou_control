from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import HomeAssistant

from .const import DOMAIN


class ImouAxisNumber(NumberEntity):
    def __init__(self, hass: HomeAssistant, device_id: str, axis: str, data: dict):
        self._hass = hass
        self._device_id = device_id
        self._axis = axis
        self._data = data
        self._attr_should_poll = False
        self._attr_mode = NumberMode.BOX
        self._attr_unique_id = f"{device_id}_{axis}"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, device_id)})
        self._attr_has_entity_name = True
        key = "horizontal" if axis == "h" else "vertical"
        self._attr_translation_key = key

        self._attr_native_min_value = -1.0
        self._attr_native_max_value = 1.0
        self._attr_native_step = 0.01
        self._attr_native_value = data["coords"][axis]

    async def async_set_native_value(self, value: float) -> None:
        self._data["coords"][self._axis] = float(value)
        self._attr_native_value = float(value)
        self.async_write_ha_state()


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, dev in data["devices"].items():
        entities.append(ImouAxisNumber(hass, device_id, "h", dev))
        entities.append(ImouAxisNumber(hass, device_id, "v", dev))
    async_add_entities(entities)
