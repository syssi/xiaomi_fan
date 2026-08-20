"""Select platform for the Xiaomi Mi Smart Pedestal Fan oscillation angle.

Exposes the horizontal oscillation angle of the dmaker.fan.* MIOT fans
(P5/P9/P10/P11/P15/P18/P30) as a Home Assistant ``select`` entity, so the
angle can be chosen from the UI (a dropdown) instead of only via the
``xiaomi_miio_fan.fan_set_oscillation_angle`` service.

Example configuration.yaml:

    select:
      - platform: xiaomi_miio_fan
        name: Ventilador Dormitorio - Angulo Oscilacion
        host: 192.168.168.138
        token: !secret xiaomi_fan_dormitorio_token
        model: dmaker.fan.p18
"""

import logging

from homeassistant.const import CONF_HOST, CONF_NAME, CONF_TOKEN
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv
from miio import Device, DeviceException, FanMiot, FanP5
import voluptuous as vol

try:
    # Home Assistant >= 2022.x
    from homeassistant.components.select import SelectEntity
except ImportError:  # pragma: no cover
    from homeassistant.components.select.entity import SelectEntity

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi Miio Fan Angle"
CONF_MODEL = "model"

MODEL_FAN_P5 = "dmaker.fan.p5"
MODEL_FAN_P9 = "dmaker.fan.p9"
MODEL_FAN_P10 = "dmaker.fan.p10"
MODEL_FAN_P11 = "dmaker.fan.p11"
MODEL_FAN_P15 = "dmaker.fan.p15"
MODEL_FAN_P18 = "dmaker.fan.p18"
MODEL_FAN_P30 = "dmaker.fan.p30"

# Angles accepted by python-miio's set_angle() per fan family.
ANGLES_DEFAULT = [30, 60, 90, 120, 140]
MODEL_TO_ANGLES = {
    MODEL_FAN_P5: [30, 60, 90, 120],
    MODEL_FAN_P9: [30, 60, 90, 120, 140],
    MODEL_FAN_P10: [30, 60, 90, 120, 140],
    MODEL_FAN_P11: [30, 60, 90, 120, 140],
    MODEL_FAN_P15: [30, 60, 90, 120, 140],
    MODEL_FAN_P18: [30, 60, 90, 120, 140],
    MODEL_FAN_P30: [30, 60, 90, 120, 140],
}

PLATFORM_SCHEMA = cv.PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODEL): cv.string,
    }
)


def _build_device(host, token, model):
    """Instantiate the proper python-miio device for the given model.

    Mirrors the mapping used by fan.py so aliased models (e.g. P18 -> P10)
    talk to the fan with the correct MIOT mapping.
    """
    if model in (MODEL_FAN_P10, MODEL_FAN_P18, MODEL_FAN_P30):
        return FanMiot(host, token, model=MODEL_FAN_P10)
    if model in (MODEL_FAN_P11, MODEL_FAN_P15):
        return FanMiot(host, token, model=MODEL_FAN_P11)
    if model == MODEL_FAN_P9:
        return FanMiot(host, token, model=MODEL_FAN_P9)
    if model == MODEL_FAN_P5:
        return FanP5(host, token, model=model)
    # Fallback: most dmaker MIOT fans behave like the P10.
    return FanMiot(host, token, model=MODEL_FAN_P10)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the oscillation-angle select from configuration.yaml."""
    host = config[CONF_HOST]
    token = config[CONF_TOKEN]
    name = config[CONF_NAME]
    model = config.get(CONF_MODEL)

    mac = None
    try:
        device_info = await hass.async_add_executor_job(Device(host, token).info)
        if model is None:
            model = device_info.model
        mac = device_info.mac_address
    except DeviceException as ex:
        if model is None:
            raise PlatformNotReady from ex
        _LOGGER.warning("Could not read device info (%s); continuing with model %s", ex, model)

    angles = MODEL_TO_ANGLES.get(model, ANGLES_DEFAULT)
    device = _build_device(host, token, model)
    unique_id = f"{model}-{mac}-oscillation_angle" if mac else None

    _LOGGER.info("Adding oscillation-angle select for %s (%s), angles=%s", name, model, angles)
    async_add_entities(
        [XiaomiFanAngleSelect(name, device, model, unique_id, angles)],
        update_before_add=True,
    )


class XiaomiFanAngleSelect(SelectEntity):
    """A select entity representing the fan's horizontal oscillation angle."""

    _attr_icon = "mdi:angle-acute"

    def __init__(self, name, device, model, unique_id, angles):
        self._device = device
        self._model = model
        self._angles = angles
        self._attr_name = name
        self._attr_unique_id = unique_id
        self._attr_options = [str(a) for a in angles]
        self._attr_current_option = None
        self._attr_available = False

    async def async_update(self):
        """Poll the fan for its current oscillation angle."""
        try:
            state = await self.hass.async_add_executor_job(self._device.status)
            angle = getattr(state, "angle", None)
            self._attr_available = True
            if angle is not None:
                self._attr_current_option = str(angle)
        except DeviceException as ex:
            self._attr_available = False
            _LOGGER.debug("Error fetching angle for %s: %s", self._attr_name, ex)

    async def async_select_option(self, option: str) -> None:
        """Set a new oscillation angle."""
        try:
            angle = int(option)
        except (TypeError, ValueError):
            _LOGGER.error("Invalid angle option: %s", option)
            return
        if angle not in self._angles:
            _LOGGER.error(
                "Invalid angle %s; allowed values are %s",
                angle,
                ", ".join(str(a) for a in self._angles),
            )
            return
        try:
            await self.hass.async_add_executor_job(self._device.set_angle, angle)
            self._attr_current_option = option
        except DeviceException as ex:
            _LOGGER.error("Setting angle of the miio device failed: %s", ex)
