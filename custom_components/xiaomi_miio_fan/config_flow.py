"""Config flow for Xiaomi Mi Smart Pedestal Fan."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.core import callback
from miio import Device, DeviceException

from .const import (
    CONF_MODEL,
    CONF_PRESET_MODES_OVERRIDE,
    CONF_RETRIES,
    DEFAULT_NAME,
    DEFAULT_RETRIES,
    DOMAIN,
    SUPPORTED_MODELS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_TOKEN): vol.All(str, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_MODEL, default=""): vol.In([""] + SUPPORTED_MODELS),
    }
)


class XiaomiFanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xiaomi Mi Smart Pedestal Fan."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ):
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            token = user_input[CONF_TOKEN]
            model = user_input.get(CONF_MODEL) or None

            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            try:
                miio_device = Device(host, token)
                device_info = await self.hass.async_add_executor_job(miio_device.info)
                if model is None:
                    model = device_info.model
                    user_input[CONF_MODEL] = model
            except DeviceException:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during config flow")
                errors["base"] = "unknown"

            if not errors:
                name = user_input.get(CONF_NAME) or DEFAULT_NAME
                return self.async_create_entry(title=name, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return XiaomiFanOptionsFlow()


class XiaomiFanOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Xiaomi Mi Smart Pedestal Fan."""

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None):
        """Manage the options."""
        if user_input is not None:
            pmo_raw = (user_input.get(CONF_PRESET_MODES_OVERRIDE) or "").strip()
            user_input[CONF_PRESET_MODES_OVERRIDE] = (
                [m.strip() for m in pmo_raw.split(",") if m.strip()] if pmo_raw else None
            )
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        pmo = opts.get(CONF_PRESET_MODES_OVERRIDE)
        pmo_str = ", ".join(pmo) if isinstance(pmo, list) else ""

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_RETRIES,
                    default=opts.get(CONF_RETRIES, DEFAULT_RETRIES),
                ): vol.All(int, vol.Range(min=1, max=100)),
                vol.Optional(CONF_PRESET_MODES_OVERRIDE, default=pmo_str): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
