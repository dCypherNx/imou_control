from __future__ import annotations
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, CONF_APP_ID, CONF_APP_SECRET, CONF_URL_BASE
from .token_manager import TokenManager
from .api import ApiClient

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    app_id     = entry.data[CONF_APP_ID]
    app_secret = entry.data[CONF_APP_SECRET]
    url_base   = entry.data[CONF_URL_BASE]

    tm  = TokenManager(app_id, app_secret, url_base)
    api = ApiClient(app_id, app_secret, url_base, tm.get_token, tm.refresh_token)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"tm": tm, "api": api}

    async def srv_set_position(call: ServiceCall):
        device_id = call.data["device_id"]
        h = float(call.data["h"])
        v = float(call.data["v"])
        z = float(call.data.get("z", 0.0))
        try:
            ok = await api.set_position(device_id, h, v, z)
            if not ok:
                _LOGGER.warning("set_position retornou False para %s", device_id)
        except Exception as e:
            _LOGGER.exception("Falha em set_position para %s: %s", device_id, e)
            raise

    hass.services.async_register(
        DOMAIN, "set_position", srv_set_position,
        schema=vol.Schema({
            vol.Required("device_id"): cv.string,
            vol.Required("h"): vol.Coerce(float),
            vol.Required("v"): vol.Coerce(float),
            vol.Optional("z", default=0.0): vol.Coerce(float),
        })
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
