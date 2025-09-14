from __future__ import annotations

import logging

import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .api import ApiClient
from .const import (
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_URL_BASE,
    DOMAIN,
    SIGNAL_NEW_DEVICE,
)
from .token_manager import TokenManager

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["select"]

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    app_id     = entry.data[CONF_APP_ID]
    app_secret = entry.data[CONF_APP_SECRET]
    url_base   = entry.data[CONF_URL_BASE]

    session = async_create_clientsession(hass)
    tm = TokenManager(app_id, app_secret, url_base, session)
    api = ApiClient(
        app_id,
        app_secret,
        url_base,
        tm.async_get_token,
        session,
        tm.async_refresh_token,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "tm": tm,
        "api": api,
        "session": session,
        "devices": [],
    }

    async def async_add_device(device: dict) -> None:
        """Add a discovered/configured device and notify listeners."""
        devices = hass.data[DOMAIN][entry.entry_id]["devices"]
        devices.append(device)
        async_dispatcher_send(hass, SIGNAL_NEW_DEVICE, entry.entry_id, device)

    hass.data[DOMAIN][entry.entry_id]["add_device"] = async_add_device

    async def srv_set_position(call: ServiceCall):
        device_id = call.data["device_id"]
        h = float(call.data["h"])
        v = float(call.data["v"])
        z = float(call.data.get("z", 0.0))
        try:
            ok = await api.async_set_position(device_id, h, v, z)
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
                vol.Required("device_id"): cv.string,
                vol.Required("h"): vol.Coerce(float),
                vol.Required("v"): vol.Coerce(float),
                vol.Optional("z", default=0.0): vol.Coerce(float),
            }
        ),
    )

    async def srv_register_device(call: ServiceCall):
        """Register a device at runtime."""
        device = {
            "device_id": call.data["device_id"],
            "name": call.data.get("name"),
            "model": call.data.get("model"),
        }
        await async_add_device(device)

    hass.services.async_register(
        DOMAIN,
        "register_device",
        srv_register_device,
        schema=vol.Schema(
            {
                vol.Required("device_id"): cv.string,
                vol.Optional("name"): cv.string,
                vol.Optional("model"): cv.string,
            }
        ),
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, {})
        session = entry_data.get("session")
        if session:
            await session.close()
        unsub = entry_data.get("unsub_dispatcher")
        if unsub:
            unsub()
    return unload_ok
