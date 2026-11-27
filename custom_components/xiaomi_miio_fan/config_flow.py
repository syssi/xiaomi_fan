"""Config flow for Xiaomi Mi Smart Pedestal Fan."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant, callback
from miio import Device, DeviceException
import voluptuous as vol

from .const import (
    CONF_IMPORTED_HOST,
    CONF_MAC,
    CONF_MODEL,
    CONF_PRESET_MODES_OVERRIDE,
    CONF_RETRIES,
    DEFAULT_NAME,
    DEFAULT_RETRIES,
    DOMAIN,
    SUPPORTED_MODELS,
)

_LOGGER = logging.getLogger(__name__)

TOKEN_SCHEMA = vol.All(str, vol.Length(min=32, max=32))

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_TOKEN): TOKEN_SCHEMA,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
        vol.Optional(CONF_MODEL, default=""): vol.In(["", *SUPPORTED_MODELS]),
    }
)


class CannotConnectError(Exception):
    """Error to indicate the device did not answer with the given credentials."""


def build_unique_id(model: str, mac: str) -> str:
    """Return the unique id, identical to the one used by the YAML platform."""
    return f"{model}-{mac}"


async def async_get_device_info(
    hass: HomeAssistant, host: str, token: str
) -> tuple[str, str]:
    """Query the device and return its detected model and MAC address."""
    try:
        info = await hass.async_add_executor_job(Device(host, token).info)
    except DeviceException as ex:
        raise CannotConnectError from ex
    return info.model, info.mac_address


class XiaomiFanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle a config flow for Xiaomi Mi Smart Pedestal Fan."""

    VERSION = 1

    async def _async_validate(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> tuple[str, str] | None:
        """Connect to the device and fill errors on failure."""
        try:
            detected_model, mac = await async_get_device_info(
                self.hass, user_input[CONF_HOST], user_input[CONF_TOKEN]
            )
        except CannotConnectError:
            errors["base"] = "cannot_connect"
            return None
        except Exception:
            _LOGGER.exception("Unexpected exception during config flow")
            errors["base"] = "unknown"
            return None
        return detected_model, mac

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            result = await self._async_validate(user_input, errors)
            if result is not None:
                detected_model, mac = result
                model = user_input.get(CONF_MODEL) or detected_model
                if model not in SUPPORTED_MODELS:
                    errors["base"] = "unsupported_model"
                else:
                    await self.async_set_unique_id(build_unique_id(detected_model, mac))
                    # A known fan re-added with a new IP or token updates the entry.
                    self._abort_if_unique_id_configured(
                        updates={
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_TOKEN: user_input[CONF_TOKEN],
                        }
                    )
                    name = user_input.get(CONF_NAME) or DEFAULT_NAME
                    return self.async_create_entry(
                        title=name,
                        data={
                            CONF_HOST: user_input[CONF_HOST],
                            CONF_TOKEN: user_input[CONF_TOKEN],
                            CONF_NAME: name,
                            CONF_MODEL: model,
                            CONF_MAC: mac,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Change host and token of an existing fan."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            result = await self._async_validate(user_input, errors)
            if result is not None:
                detected_model, mac = result
                await self.async_set_unique_id(build_unique_id(detected_model, mac))
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_TOKEN: user_input[CONF_TOKEN],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_TOKEN): TOKEN_SCHEMA,
            }
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or {CONF_HOST: entry.data[CONF_HOST]}
            ),
            errors=errors,
        )

    async def async_step_import(
        self, import_data: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Import a fan configured in YAML."""
        host = import_data[CONF_HOST]
        token = import_data[CONF_TOKEN]
        try:
            detected_model, mac = await async_get_device_info(self.hass, host, token)
        except CannotConnectError:
            return self.async_abort(reason="cannot_connect")

        model = import_data.get(CONF_MODEL) or detected_model
        if model not in SUPPORTED_MODELS:
            return self.async_abort(reason="unsupported_model")

        await self.async_set_unique_id(build_unique_id(detected_model, mac))
        self._abort_if_unique_id_configured()

        name = import_data.get(CONF_NAME) or DEFAULT_NAME
        return self.async_create_entry(
            title=name,
            data={
                CONF_HOST: host,
                CONF_TOKEN: token,
                CONF_NAME: name,
                CONF_MODEL: model,
                CONF_MAC: mac,
                # Lets a later restart recognise the YAML entry after host changes.
                CONF_IMPORTED_HOST: host,
            },
            options={
                CONF_RETRIES: import_data.get(CONF_RETRIES, DEFAULT_RETRIES),
                CONF_PRESET_MODES_OVERRIDE: import_data.get(CONF_PRESET_MODES_OVERRIDE),
            },
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

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            pmo_raw = (user_input.get(CONF_PRESET_MODES_OVERRIDE) or "").strip()
            user_input[CONF_PRESET_MODES_OVERRIDE] = (
                [m.strip() for m in pmo_raw.split(",") if m.strip()]
                if pmo_raw
                else None
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
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=100)),
                vol.Optional(CONF_PRESET_MODES_OVERRIDE, default=pmo_str): str,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
