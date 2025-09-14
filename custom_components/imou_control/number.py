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

    @property
    def name(self) -> str:
        axis_name = {"h": "Horizontal", "v": "Vertical"}.get(self._axis, self._axis)
        return f"{self._data['name']} {axis_name}"

    @property
    def unique_id(self) -> str:
        return f"{self._device_id}_{self._axis}"

    @property
    def min_value(self) -> float:
        return -1.0

    @property
    def max_value(self) -> float:
        return 1.0

    @property
    def step(self) -> float:
        return 0.01

    @property
    def value(self) -> float:
        return self._data["coords"][self._axis]

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(identifiers={(DOMAIN, self._device_id)})

    async def async_set_value(self, value: float) -> None:
        self._data["coords"][self._axis] = float(value)
        self.async_write_ha_state()

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    entities = []
    for device_id, dev in data["devices"].items():
        entities.append(ImouAxisNumber(hass, device_id, "h", dev))
        entities.append(ImouAxisNumber(hass, device_id, "v", dev))
    async_add_entities(entities)
