from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .usage import ApiUsageTracker


@dataclass
class _UsageData:
    tracker: ApiUsageTracker
    entry_id: str


class ImouApiUsageSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "api_usage"
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = None
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, data: _UsageData) -> None:
        self._tracker = data.tracker
        self._entry_id = data.entry_id
        self._remove_listener: Callable[[], None] | None = None
        self._attr_unique_id = f"{self._entry_id}_api_usage"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"account_{self._entry_id}")},
            manufacturer="Imou",
            name="Imou Account",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._remove_listener = self._tracker.async_add_listener(self.async_write_ha_state)
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self) -> None:
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None
        await super().async_will_remove_from_hass()

    @property
    def native_value(self) -> int:
        return self._tracker.count

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        attrs: dict[str, str | None] = {}
        period = self._tracker.period
        if period is not None:
            attrs["period"] = period

        last_reset = self._tracker.last_reset
        if last_reset:
            attrs["last_reset"] = self._format_dt(last_reset)

        last_call = self._tracker.last_call
        if last_call:
            attrs["last_call"] = self._format_dt(last_call)

        return attrs

    @staticmethod
    def _format_dt(value: datetime) -> str:
        return value.isoformat()


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    tracker: ApiUsageTracker = data["usage"]
    async_add_entities([ImouApiUsageSensor(_UsageData(tracker, entry.entry_id))])
