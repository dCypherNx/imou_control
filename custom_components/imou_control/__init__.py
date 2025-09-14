from __future__ import annotations
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_URL_BASE,
    EVENT_PRESET_CALLED,
)
from .token_manager import TokenManager
from .api import ApiClient

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    app_id     = entry.data[CONF_APP_ID]
    app_secret = entry.data[CONF_APP_SECRET]
    url_base   = entry.data[CONF_URL_BASE]

    tm = TokenManager(app_id, app_secret, url_base)
    api = ApiClient(app_id, app_secret, url_base, tm.get_token, tm.refresh_token)

    hass.data.setdefault(DOMAIN, {})
    data_entry = hass.data[DOMAIN][entry.entry_id] = {
        "tm": tm,
        "api": api,
        "devices": {},
        "devices_by_name": {},
    }

    registry = dr.async_get(hass)
    try:
        devices_info = await hass.async_add_executor_job(api.list_devices)
    except Exception as err:
        _LOGGER.error("Não foi possível obter a lista de dispositivos: %s", err)
        devices_info = []
    for info in devices_info:
        device_id = info.get("deviceId")
        name = info.get("deviceName", f"Imou {device_id}")
        data_entry["devices"][device_id] = {
            "name": name,
            "presets": {},
            "last_preset": None,
            "coords": {"h": 0.0, "v": 0.0, "z": 0.0},
            "select_entity": None,
        }
        data_entry["devices_by_name"][name] = device_id
        registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device_id)},
            manufacturer="Imou",
            name=name,
        )

    await hass.config_entries.async_forward_entry_setups(entry, ["number", "select"])

    def resolve_device_id(device: str) -> str | None:
        if device in data_entry["devices"]:
            return device
        return data_entry["devices_by_name"].get(device)

    async def srv_set_position(call: ServiceCall):
        device = call.data["device"]
        device_id = resolve_device_id(device)
        if not device_id:
            _LOGGER.warning("Dispositivo %s não encontrado", device)
            return
        h = float(call.data["h"])
        v = float(call.data["v"])
        z = float(call.data.get("z", 0.0))
        try:
            ok = await hass.async_add_executor_job(api.set_position, device_id, h, v, z)
            if not ok:
                _LOGGER.warning("set_position retornou False para %s", device_id)
        except Exception as e:
            _LOGGER.exception("Falha em set_position para %s: %s", device_id, e)
            raise

    hass.services.async_register(
        DOMAIN,
        "set_position",
        srv_set_position,
        schema=vol.Schema(
            {
                vol.Required("device"): cv.string,
                vol.Required("h"): vol.Coerce(float),
                vol.Required("v"): vol.Coerce(float),
                vol.Optional("z", default=0.0): vol.Coerce(float),
            }
        ),
    )

    async def srv_define_preset(call: ServiceCall):
        device = call.data["device"]
        device_id = resolve_device_id(device)
        if not device_id:
            _LOGGER.warning("Dispositivo %s não encontrado", device)
            return
        preset = call.data["preset"]
        h = float(call.data["h"])
        v = float(call.data["v"])
        z = float(call.data.get("z", 0.0))

        data = hass.data[DOMAIN][entry.entry_id]
        dev = data["devices"][device_id]
        if preset in dev["presets"]:
            _LOGGER.warning("Preset %s já definido para %s", preset, device_id)
            return
        dev["presets"][preset] = (h, v, z)
        sel = dev.get("select_entity")
        if sel is not None:
            sel.async_update_presets()

    hass.services.async_register(
        DOMAIN,
        "define_preset",
        srv_define_preset,
        schema=vol.Schema(
            {
                vol.Required("device"): cv.string,
                vol.Required("preset"): cv.string,
                vol.Required("h"): vol.Coerce(float),
                vol.Required("v"): vol.Coerce(float),
                vol.Optional("z", default=0.0): vol.Coerce(float),
            }
        ),
    )

    async def srv_call_preset(call: ServiceCall):
        device = call.data["device"]
        device_id = resolve_device_id(device)
        if not device_id:
            _LOGGER.warning("Dispositivo %s não encontrado", device)
            return
        preset = call.data["preset"]

        data = hass.data[DOMAIN][entry.entry_id]
        devices = data["devices"]
        dev = devices.get(device_id)
        if not dev:
            _LOGGER.warning("Dispositivo %s não encontrado", device_id)
            return
        coords = dev["presets"].get(preset)
        if coords is None:
            _LOGGER.warning("Preset %s não definido para %s", preset, device_id)
            return
        if dev.get("last_preset") == preset:
            _LOGGER.debug("Preset %s já ativo em %s, ignorando", preset, device_id)
            return
        h, v, z = coords
        try:
            await hass.async_add_executor_job(api.set_position, device_id, h, v, z)
            dev["last_preset"] = preset
            hass.bus.async_fire(
                EVENT_PRESET_CALLED,
                {"device": device_id, "preset": preset},
                context=call.context,
            )
        except Exception as e:
            _LOGGER.exception(
                "Falha ao acionar preset %s em %s: %s", preset, device_id, e
            )

    hass.services.async_register(
        DOMAIN,
        "call_preset",
        srv_call_preset,
        schema=vol.Schema(
            {
                vol.Required("device"): cv.string,
                vol.Required("preset"): cv.string,
            }
        ),
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    await hass.config_entries.async_unload_platforms(entry, ["number", "select"])
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
