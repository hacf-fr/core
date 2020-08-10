"""Constants for the Enedis integration."""

DOMAIN = "enedis"

OAUTH2_AUTHORIZE = "http://www.sud-domotique-expert.fr/enedis/accord_enedis_prod.html"
OAUTH2_TOKEN = "http://www.sud-domotique-expert.fr/enedis/enedis_token_prod.php"

AUTH_CALLBACK_PATH = "/auth/enedis/callback"
AUTH_CALLBACK_NAME = "auth:enedis:callback"

CONF_REFRESH_TOKEN = "refresh_token"
CONF_ACCESS_TOKEN = "access_token"
CONF_USAGE_POINT_ID = "usage_point_id"
