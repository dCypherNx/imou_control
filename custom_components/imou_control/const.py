DOMAIN = "imou_control"

# Credenciais configuradas no config_flow
CONF_APP_ID = "app_id"
CONF_APP_SECRET = "app_secret"
CONF_URL_BASE = "url_base"

# Endpoints padrão da Open API (relativos ao url_base)
TOKEN_ENDPOINT = "/openapi/accessToken"
PTZ_LOCATION_ENDPOINT = "/openapi/controlLocationPTZ"

# Sinal usado para notificar novas câmeras descobertas/configuradas
SIGNAL_NEW_DEVICE = "imou_control_new_device"
