DOMAIN = "imou_control"

# Credenciais configuradas no config_flow
CONF_APP_ID = "app_id"
CONF_APP_SECRET = "app_secret"
CONF_URL_BASE = "url_base"

# Endpoints padrão da Open API (relativos ao url_base)
TOKEN_ENDPOINT = "/openapi/accessToken"
PTZ_LOCATION_ENDPOINT = "/openapi/controlLocationPTZ"
DEVICE_LIST_ENDPOINT = "/openapi/device/list"

# Nome do evento disparado quando um preset é chamado
EVENT_PRESET_CALLED = "imou_control_preset_called"
