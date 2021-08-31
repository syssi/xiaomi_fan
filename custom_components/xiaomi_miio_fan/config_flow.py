"""Config flow to configure Xiaomi Fan/AirPurifier component."""
from collections import OrderedDict
from typing import Optional

import voluptuous as vol
from homeassistant.config_entries import (
    CONN_CLASS_LOCAL_PUSH,
    ConfigFlow,
    OptionsFlow,
    ConfigEntry
    )
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME, CONF_HOST, CONF_TOKEN
from homeassistant.core import callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.util.network import is_ip_address
from homeassistant.exceptions import PlatformNotReady
from miio import (  # pylint: disable=import-error
    Device,
    DeviceException
)
from .const import (
    AUTO_DETECT,
    DEFAULT_NAME,
    DEFAULT_RETRIES,
    DOMAIN,
    CONF_MODEL,
    CONF_RETRIES,
    CONF_PRESET_MODES_OVERRIDE,
    OPT_MODEL,
    OPT_PRESET_MODE
)


def is_supported_model(host, token, model):
    try:
        miio_device = Device(host, token)
        device_info = miio_device.info()
        miio_model = device_info.model
        if model == AUTO_DETECT and miio_model in OPT_MODEL:
            return miio_model
        if miio_model == model and miio_model in OPT_MODEL:
            return miio_model
    except DeviceException as ex:
        raise PlatformNotReady from ex
    return None


class FanFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Xiaomi Fan Component config flow."""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_PUSH

    def __init__(self):
        """Initialize flow."""
        self._host: Optional[str] = None
        self._token: Optional[str] = None
        self._model: Optional[str] = None

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry):
        """ get option flow """
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self,
        user_input: Optional[ConfigType] = None,
        error: Optional[str] = None
    ):  # pylint: disable=arguments-differ
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self._set_user_input(user_input)
            if not is_ip_address(self._host):
                return self.async_abort(reason="connection_error")
            try:
                bytes.fromhex(self._token)
            except ValueError:
                return self.async_abort(reason="connection_error")
            model = is_supported_model(self._host, self._token, self._model)
            if model is None:
                return self.async_abort(reason="model_error")
            self._model = model
            self._name = OPT_MODEL.get(model, DEFAULT_NAME)
            await self.async_set_unique_id(self._host)

            return self._async_get_entry()

        fields = OrderedDict()
        fields[vol.Required(CONF_HOST,
                            default=self._host or vol.UNDEFINED)] = str
        fields[vol.Required(CONF_TOKEN,
                            default=self._token or vol.UNDEFINED)] = str
        fields[vol.Optional(CONF_MODEL,
                            default=self._model or AUTO_DETECT)] = vol.In(
                                OPT_MODEL)

        for entry in self._async_current_entries():
            already_configured = False
            if CONF_HOST in entry.data and entry.data[CONF_HOST] in [
                self._host
            ]:
                # Is this address or IP address already configured?
                already_configured = True
            elif CONF_HOST in entry.options and entry.options[CONF_HOST] in [
                self._host
            ]:
                # Is this address or IP address already configured?
                already_configured = True
            if already_configured:
                # Backwards compat, we update old entries

                return self.async_abort(reason="already_configured")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(fields),
            errors={'base': error} if error else None
        )

    @property
    def _name(self):
        # pylint: disable=no-member
        # https://github.com/PyCQA/pylint/issues/3167
        return self.context.get(CONF_NAME)

    @_name.setter
    def _name(self, value):
        # pylint: disable=no-member
        # https://github.com/PyCQA/pylint/issues/3167
        self.context[CONF_NAME] = value
        self.context["title_placeholders"] = {"name": self._name}

    def _set_user_input(self, user_input):
        if user_input is None:
            return
        self._host = user_input.get(CONF_HOST, "")
        self._token = user_input.get(CONF_TOKEN, "")
        self._model = user_input.get(CONF_MODEL, "")

    @callback
    def _async_get_entry(self):
        return self.async_create_entry(
            title=self._name,
            data={
                CONF_HOST: self._host,
                CONF_TOKEN: self._token,
                CONF_MODEL: self._model
            }
        )


class OptionsFlowHandler(OptionsFlow):
    # pylint: disable=too-few-public-methods
    """Handle options flow changes."""
    _host = None
    _token = None
    _model = None
    _retries = None
    _preset_modes_override = None

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            if not is_ip_address(user_input.get(CONF_HOST)):
                return self.async_abort(reason="connection_error")
            self._host = user_input.get(CONF_HOST)
            if len(user_input.get(CONF_TOKEN, '')) >= 1:
                self._token = user_input.get(CONF_TOKEN)
            self._model = user_input.get(CONF_MODEL)
            model = is_supported_model(self._host, self._token, self._model)
            if model is None:
                return self.async_abort(reason="model_error")
            self._model = model
            self._name = OPT_MODEL.get(model, DEFAULT_NAME)
            self._retries = user_input.get(CONF_RETRIES, DEFAULT_RETRIES)
            self._preset_modes_override = user_input.get(CONF_PRESET_MODES_OVERRIDE, [])

            return self.async_create_entry(
                title='',
                data={
                    CONF_HOST: self._host,
                    CONF_TOKEN: self._token,
                    CONF_MODEL: self._model,
                    CONF_RETRIES: self._retries,
                    CONF_PRESET_MODES_OVERRIDE: self._preset_modes_override,
                }
            )
        self._host = self.config_entry.options.get(CONF_HOST, '')
        self._token = self.config_entry.options.get(CONF_TOKEN, '')
        self._model = self.config_entry.options.get(CONF_MODEL, '')
        self._retries = self.config_entry.options.get(CONF_RETRIES, DEFAULT_RETRIES)
        self._preset_modes_override = self.config_entry.options.get(
            CONF_PRESET_MODES_OVERRIDE, [])

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self._host): str,
                    vol.Required(CONF_TOKEN, default=self._token): str,
                    vol.Optional(CONF_MODEL, default=self._model): vol.In(
                                OPT_MODEL),
                    vol.Optional(CONF_RETRIES, default=self._retries): int,
                    vol.Optional(
                        CONF_PRESET_MODES_OVERRIDE,
                        default=self._preset_modes_override): cv.multi_select(
                            OPT_PRESET_MODE)
                }
            )
        )
