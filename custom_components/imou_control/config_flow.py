from __future__ import annotations
from typing import Any, Dict
import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, CONF_APP_ID, CONF_APP_SECRET, CONF_URL_BASE

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({
    # Tudo como string (como na sua versão que funcionava)
    vol.Required(CONF_APP_ID): cv.string,
    vol.Required(CONF_APP_SECRET): cv.string,
    vol.Required(CONF_URL_BASE): cv.string,  # sem cv.url para evitar 500 por validação
})

class ImouControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Fluxo mínimo e robusto para Imou Control."""
    VERSION = 1

    async def async_step_user(self, user_input: Dict[str, Any] | None = None):
        try:
            # Permite apenas 1 entrada
            if self._async_current_entries():
                return self.async_abort(reason="single_instance_allowed")

            if user_input is not None:
                title = "Imou Control"
                return self.async_create_entry(
                    title=title,
                    data={
                        CONF_APP_ID: user_input[CONF_APP_ID],
                        CONF_APP_SECRET: user_input[CONF_APP_SECRET],
                        CONF_URL_BASE: user_input[CONF_URL_BASE],
                    },
                )

            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)

        except Exception:
            _LOGGER.exception("imou_control: exception in config flow")
            # Evita 500 e volta o formulário
            return self.async_show_form(
                step_id="user",
                data_schema=DATA_SCHEMA,
                errors={"base": "unexpected_error"},
            )
