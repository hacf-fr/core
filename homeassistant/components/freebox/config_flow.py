"""Config flow to configure the Freebox integration."""
import logging

from freebox_api.exceptions import AuthorizationError, HttpRequestError
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import ssdp
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import DOMAIN
from .router import get_api

_LOGGER = logging.getLogger(__name__)

DISCOVERY = {
    "host": "192.168.0.254",
    "port": 80,
    "hostname": "Freebox-Server.local.",
    "properties": {
        "api_version": "8.0",
        "device_type": "FreeboxServer1,2",
        "api_base_url": "/api/",
        "uid": "b15ab20debb399f95001a9ca207d2777",
        "https_available": "1",
        "https_port": "51678",
        "box_model": "fbxgw-r2/full",
        "box_model_name": "Freebox Server (r2)",
        "api_domain": "61ko051s.fbxos.fr",
    },
}

SSDP = {
    "ssdp_location": "http://192.168.0.254:5678/desc/root",
    "ssdp_st": "urn:schemas-upnp-org:service:WANIPConnection:2",
    "deviceType": "urn:schemas-upnp-org:device:InternetGatewayDevice:2",
    "friendlyName": "Freebox Server",
    "manufacturer": "Freebox",
    "manufacturerURL": "http://www.freebox.fr/",
    "modelDescription": "NAS/Modem/Routeur ADSL/FTTH",
    "modelName": "Freebox Server",
    "modelNumber": "6",
    "modelURL": "http://www.freebox.fr/",
    "serialNumber": "68A37863C212",
    "UDN": "uuid:igd73616d61-6a65-7374-650a-68a37863c212",
    "serviceList": {
        "service": {
            "serviceType": "urn:schemas-upnp-org:service:Layer3Forwarding:1",
            "serviceId": "urn:upnp-org:serviceId:L3Forwarding1",
            "SCPDURL": "/desc/l3f",
            "controlURL": "/control/l3f",
            "eventSubURL": "/event/l3f",
        }
    },
    "deviceList": {
        "device": {
            "deviceType": "urn:schemas-upnp-org:device:WANDevice:2",
            "friendlyName": "Freebox Server",
            "manufacturer": "Freebox",
            "manufacturerURL": "http://www.freebox.fr/",
            "modelDescription": "NAS/Modem/Routeur ADSL/FTTH",
            "modelName": "Freebox Server",
            "modelNumber": "6",
            "modelURL": "http://www.freebox.fr/",
            "serialNumber": "68A37863C212",
            "UDN": "uuid:wan73616d61-6a65-7374-650a-68a37863c212",
            "serviceList": {
                "service": {
                    "serviceType": "urn:schemas-upnp-org:service:WANCommonInterfaceConfig:1",
                    "serviceId": "urn:upnp-org:serviceId:WANCommonIFC1",
                    "SCPDURL": "/desc/wan_common_ifc",
                    "controlURL": "/control/wan_common_ifc",
                    "eventSubURL": "/event/wan_common_ifc",
                }
            },
            "deviceList": {
                "device": {
                    "deviceType": "urn:schemas-upnp-org:device:WANConnectionDevice:2",
                    "friendlyName": "WAN Connection Device",
                    "manufacturer": "Freebox",
                    "manufacturerURL": "http://www.freebox.fr/",
                    "modelDescription": "NAS/Modem/Routeur ADSL/FTTH",
                    "modelName": "Freebox Server",
                    "modelNumber": "6",
                    "modelURL": "http://www.freebox.fr/",
                    "serialNumber": "68A37863C212",
                    "UDN": "uuid:wanc73616d61-6a65-7374-650a-68a37863c212",
                    "serviceList": {
                        "service": {
                            "serviceType": "urn:schemas-upnp-org:service:WANIPConnection:2",
                            "serviceId": "urn:upnp-org:serviceId:WANIPConn1",
                            "SCPDURL": "/desc/wan_ip_connection",
                            "controlURL": "/control/wan_ip_connection",
                            "eventSubURL": "/event/wan_ip_connection",
                        }
                    },
                }
            },
        }
    },
    "presentationURL": "http://mafreebox.freebox.fr/",
    "ssdp_usn": "uuid:wanc73616d61-6a65-7374-650a-68a37863c212::urn:schemas-upnp-org:service:WANIPConnection:2",
    "ssdp_ext": "",
    "ssdp_server": "Linux/2.6 UPnP/1.0 fbxigdd/1.1",
}


class FreeboxFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self):
        """Initialize Freebox config flow."""
        self._host = None
        self._port = None

    def _show_setup_form(self, user_input=None, errors=None):
        """Show the setup form to the user."""

        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, "")): str,
                    vol.Required(CONF_PORT, default=user_input.get(CONF_PORT, "")): int,
                }
            ),
            errors=errors or {},
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is None:
            return self._show_setup_form(user_input, errors)

        self._host = user_input[CONF_HOST]
        self._port = user_input[CONF_PORT]

        # Check if already configured
        await self.async_set_unique_id(self._host)
        self._abort_if_unique_id_configured()

        return await self.async_step_link()

    # async def async_step_ssdp(self, discovery_info):
    #     """Handle a discovered Freebox."""
    #     _LOGGER.warn("async_step_ssdp")
    #     _LOGGER.debug(discovery_info)
    #     parsed_url = urlparse(discovery_info[ssdp.ATTR_SSDP_PROPERTIES])
    #     friendly_name = (
    #         discovery_info[ssdp.ATTR_UPNP_FRIENDLY_NAME].split("(", 1)[0].strip()
    #     )

    #     mac = discovery_info[ssdp.ATTR_UPNP_SERIAL].upper()
    #     # Synology NAS can broadcast on multiple IP addresses, since they can be connected to multiple ethernets.
    #     # The serial of the NAS is actually its MAC address.
    #     if self._mac_already_configured(mac):
    #         return self.async_abort(reason="already_configured")

    #     await self.async_set_unique_id(mac)
    #     self._abort_if_unique_id_configured()
    #     return await self.async_step_user()

    async def async_step_link(self, user_input=None):
        """Attempt to link with the Freebox router.

        Given a configured host, will ask the user to press the button
        to connect to the router.
        """
        if user_input is None:
            return self.async_show_form(step_id="link")

        errors = {}

        fbx = await get_api(self.hass, self._host)
        try:
            # Open connection and check authentication
            await fbx.open(self._host, self._port)

            # Check permissions
            await fbx.system.get_config()
            await fbx.lan.get_hosts_list()
            await self.hass.async_block_till_done()

            # Close connection
            await fbx.close()

            return self.async_create_entry(
                title=self._host,
                data={CONF_HOST: self._host, CONF_PORT: self._port},
            )

        except AuthorizationError as error:
            _LOGGER.error(error)
            errors["base"] = "register_failed"

        except HttpRequestError:
            _LOGGER.error("Error connecting to the Freebox router at %s", self._host)
            errors["base"] = "cannot_connect"

        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Unknown error connecting with Freebox router at %s", self._host
            )
            errors["base"] = "unknown"

        return self.async_show_form(step_id="link", errors=errors)

    async def async_step_import(self, user_input=None):
        """Import a config entry."""
        return await self.async_step_user(user_input)

    async def async_step_zeroconf(self, discovery_info: dict):
        """Initialize flow from zeroconf."""
        host = discovery_info["properties"]["api_domain"]
        port = discovery_info["properties"]["https_port"]
        return await self.async_step_user({CONF_HOST: host, CONF_PORT: port})
    async def async_step_ssdp(self, discovery_info: dict):
        """Initialize flow from SSDP."""
        _LOGGER.warn("async_step_ssdp")
        return await self.async_step_user(
            {CONF_HOST: ssdp.ATTR_UPNP_PRESENTATION_URL, CONF_PORT: 80}
        )

    async def async_step_discovery(self, discovery_info):
        """Initialize flow from discovery."""
        _LOGGER.warn("async_step_discovery")
        # _LOGGER.debug(discovery_info)
        return await self.async_step_user(discovery_info)
