"""
Support for Xiaomi Mi Smart Pedestal Fan.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/fan.xiaomi_miio/
"""
import asyncio
import logging
from enum import Enum
from functools import partial
from typing import Any, Dict, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.fan import (
    PLATFORM_SCHEMA,
    SUPPORT_DIRECTION,
    SUPPORT_OSCILLATE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
    FanEntity,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    CONF_HOST,
    CONF_NAME,
    CONF_TOKEN,
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)
from miio import (
    Device,
    DeviceException,
    Fan,
    Fan1C,
    FanLeshow,
    FanMiot,
    FanP5,
)
from miio.fan_common import FanException
from miio.fan_common import (
    LedBrightness as FanLedBrightness,
)
from miio.fan_common import MoveDirection as FanMoveDirection
from miio.fan_common import OperationMode as FanOperationMode
from miio.integrations.fan.leshow.fan_leshow import (
    OperationMode as FanLeshowOperationMode,
)
from miio.miot_device import DeviceStatus, MiotDevice

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi Miio Fan"
DEFAULT_RETRIES = 20
DATA_KEY = "fan.xiaomi_miio_fan"
DOMAIN = "xiaomi_miio_fan"

CONF_MODEL = "model"
CONF_RETRIES = "retries"
CONF_PRESET_MODES_OVERRIDE = "preset_modes_override"

MODEL_FAN_V2 = "zhimi.fan.v2"  # Pedestal Fan Fan V2
MODEL_FAN_V3 = "zhimi.fan.v3"  # Pedestal Fan Fan V3
MODEL_FAN_SA1 = "zhimi.fan.sa1"  # Pedestal Fan Fan SA1
MODEL_FAN_ZA1 = "zhimi.fan.za1"  # Pedestal Fan Fan ZA1
MODEL_FAN_ZA3 = "zhimi.fan.za3"  # Pedestal Fan Fan ZA3
MODEL_FAN_ZA4 = "zhimi.fan.za4"  # Pedestal Fan Fan ZA4
MODEL_FAN_ZA5 = "zhimi.fan.za5"  # Smartmi Standing Fan 3
MODEL_FAN_P5 = "dmaker.fan.p5"  # Pedestal Fan Fan P5
MODEL_FAN_P8 = "dmaker.fan.p8"  # Pedestal Fan Fan P8
MODEL_FAN_P9 = "dmaker.fan.p9"  # Pedestal Fan Fan P9
MODEL_FAN_P10 = "dmaker.fan.p10"  # Pedestal Fan Fan P10
MODEL_FAN_P11 = "dmaker.fan.p11"  # Mijia Pedestal Fan
MODEL_FAN_P15 = "dmaker.fan.p15"  # Pedestal Fan Fan P15
MODEL_FAN_P18 = "dmaker.fan.p18"  # Mi Smart Standing Fan 2
MODEL_FAN_P33 = "dmaker.fan.p33"  # Mi Smart Standing Fan Pro 2
MODEL_FAN_P39 = "dmaker.fan.p39"  # Smart Tower Fan
MODEL_FAN_LESHOW_SS4 = "leshow.fan.ss4"
MODEL_FAN_1C = "dmaker.fan.1c"  # Pedestal Fan Fan 1C

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MODEL): vol.In(
            [
                MODEL_FAN_V2,
                MODEL_FAN_V3,
                MODEL_FAN_SA1,
                MODEL_FAN_ZA1,
                MODEL_FAN_ZA3,
                MODEL_FAN_ZA4,
                MODEL_FAN_ZA5,
                MODEL_FAN_P5,
                MODEL_FAN_P8,
                MODEL_FAN_P9,
                MODEL_FAN_P10,
                MODEL_FAN_P11,
                MODEL_FAN_P15,
                MODEL_FAN_P18,
                MODEL_FAN_P33,
                MODEL_FAN_P39,
                MODEL_FAN_LESHOW_SS4,
                MODEL_FAN_1C,
            ]
        ),
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): cv.positive_int,
        vol.Optional(CONF_PRESET_MODES_OVERRIDE, default=None): vol.Any(
            None, [cv.string]
        ),
    }
)

SPEED_OFF = "off"

ATTR_MODEL = "model"
ATTR_BRIGHTNESS = "brightness"

ATTR_TEMPERATURE = "temperature"
ATTR_HUMIDITY = "humidity"
ATTR_LED = "led"
ATTR_LED_BRIGHTNESS = "led_brightness"
ATTR_RAW_LED_BRIGHTNESS = "raw_led_brightness"
ATTR_BUZZER = "buzzer"
ATTR_CHILD_LOCK = "child_lock"
ATTR_NATURAL_SPEED = "natural_speed"
ATTR_OSCILLATE = "oscillate"
ATTR_BATTERY = "battery"
ATTR_BATTERY_CHARGE = "battery_charge"
ATTR_BATTERY_STATE = "battery_state"
ATTR_AC_POWER = "ac_power"
ATTR_DELAY_OFF_COUNTDOWN = "delay_off_countdown"
ATTR_ANGLE = "angle"
ATTR_DIRECT_SPEED = "direct_speed"
ATTR_USE_TIME = "use_time"
ATTR_BUTTON_PRESSED = "button_pressed"
ATTR_RAW_SPEED = "raw_speed"
ATTR_IONIZER = "anion"

# Fan Leshow SS4
ATTR_ERROR_DETECTED = "error_detected"

AVAILABLE_ATTRIBUTES_FAN = {
    ATTR_ANGLE: "angle",
    ATTR_RAW_SPEED: "speed",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_AC_POWER: "ac_power",
    ATTR_OSCILLATE: "oscillate",
    ATTR_DIRECT_SPEED: "direct_speed",
    ATTR_NATURAL_SPEED: "natural_speed",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_BUZZER: "buzzer",
    ATTR_LED_BRIGHTNESS: "led_brightness",
    ATTR_USE_TIME: "use_time",
    # Additional properties of version 2 and 3
    ATTR_TEMPERATURE: "temperature",
    ATTR_HUMIDITY: "humidity",
    ATTR_BATTERY: "battery",
    ATTR_BATTERY_CHARGE: "battery_charge",
    ATTR_BUTTON_PRESSED: "button_pressed",
    # Additional properties of version 2
    ATTR_LED: "led",
    ATTR_BATTERY_STATE: "battery_state",
}

AVAILABLE_ATTRIBUTES_FAN_P5 = {
    ATTR_MODE: "mode",
    ATTR_OSCILLATE: "oscillate",
    ATTR_ANGLE: "angle",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_LED: "led",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_RAW_SPEED: "speed",
}


AVAILABLE_ATTRIBUTES_FAN_P33 = {
    ATTR_MODE: "mode",
    ATTR_OSCILLATE: "oscillate",
    ATTR_ANGLE: "angle",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_LED: "led",
    ATTR_BUZZER: "buzzer",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_RAW_SPEED: "speed",
}

AVAILABLE_ATTRIBUTES_FAN_P39 = {
    ATTR_MODE: "mode",
    ATTR_OSCILLATE: "oscillate",
    ATTR_ANGLE: "angle",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_RAW_SPEED: "speed",
}

AVAILABLE_ATTRIBUTES_FAN_LESHOW_SS4 = {
    ATTR_MODE: "mode",
    ATTR_RAW_SPEED: "speed",
    ATTR_BUZZER: "buzzer",
    ATTR_OSCILLATE: "oscillate",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_ERROR_DETECTED: "error_detected",
}

AVAILABLE_ATTRIBUTES_FAN_1C = {
    ATTR_MODE: "mode",
    ATTR_RAW_SPEED: "speed",
    ATTR_BUZZER: "buzzer",
    ATTR_OSCILLATE: "oscillate",
    ATTR_DELAY_OFF_COUNTDOWN: "delay_off_countdown",
    ATTR_LED: "led",
    ATTR_CHILD_LOCK: "child_lock",
}

AVAILABLE_ATTRIBUTES_FAN_ZA5 = {
    ATTR_ANGLE: "swing_mode_angle",
    ATTR_DIRECT_SPEED: "fan_speed",
    ATTR_NATURAL_SPEED: "fan_speed",
    ATTR_DELAY_OFF_COUNTDOWN: "power_off_time",
    ATTR_AC_POWER: "powersupply_attached",
    ATTR_OSCILLATE: "swing_mode",
    ATTR_MODE: "mode",
    ATTR_CHILD_LOCK: "child_lock",
    ATTR_BUZZER: "buzzer",
    ATTR_RAW_LED_BRIGHTNESS: "light",
    ATTR_LED_BRIGHTNESS: "light_enum",
    ATTR_TEMPERATURE: "temperature",
    ATTR_HUMIDITY: "humidity",
    ATTR_BUTTON_PRESSED: "buttons_pressed",
    # Fixed attributes
    ATTR_LED: "led",
    ATTR_RAW_SPEED: "speed_rpm",
    ATTR_BATTERY: "battery_supported",
    ATTR_BATTERY_STATE: "battery_state",
    ATTR_IONIZER: "anion",
}

FAN_SPEED_LEVEL1 = "Level 1"
FAN_SPEED_LEVEL2 = "Level 2"
FAN_SPEED_LEVEL3 = "Level 3"
FAN_SPEED_LEVEL4 = "Level 4"

FAN_PRESET_MODES = {
    SPEED_OFF: range(0, 1),
    FAN_SPEED_LEVEL1: range(1, 26),
    FAN_SPEED_LEVEL2: range(26, 51),
    FAN_SPEED_LEVEL3: range(51, 76),
    FAN_SPEED_LEVEL4: range(76, 101),
}

FAN_PRESET_MODE_VALUES = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 74,
    FAN_SPEED_LEVEL4: 100,
}

FAN_PRESET_MODE_VALUES_P5 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 70,
    FAN_SPEED_LEVEL4: 100,
}

FAN_PRESET_MODES_1C = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 2,
    FAN_SPEED_LEVEL3: 3,
}

FAN_PRESET_MODES_ZA5 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 25,
    FAN_SPEED_LEVEL2: 50,
    FAN_SPEED_LEVEL3: 75,
    FAN_SPEED_LEVEL4: 100,
}

FAN_PRESET_MODES_P33 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 70,
    FAN_SPEED_LEVEL4: 100,
}

FAN_PRESET_MODES_P39 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 70,
    FAN_SPEED_LEVEL4: 100,
}

FAN_SPEEDS_1C = list(FAN_PRESET_MODES_1C)
FAN_SPEEDS_1C.remove(SPEED_OFF)

# FIXME: Add speed level 4
FAN_SPEEDS_ZA5 = list(FAN_PRESET_MODES_ZA5)
FAN_SPEEDS_ZA5.remove(SPEED_OFF)

FAN_SPEEDS_P33 = list(FAN_PRESET_MODES_P33)
FAN_SPEEDS_P33.remove(SPEED_OFF)

FAN_SPEEDS_P39 = list(FAN_PRESET_MODES_P39)
FAN_SPEEDS_P39.remove(SPEED_OFF)

SUCCESS = ["ok"]

FEATURE_SET_BUZZER = 1
FEATURE_SET_LED = 2
FEATURE_SET_CHILD_LOCK = 4
FEATURE_SET_LED_BRIGHTNESS = 8
FEATURE_SET_OSCILLATION_ANGLE = 16
FEATURE_SET_NATURAL_MODE = 32
FEATURE_SET_ANION = 64

FEATURE_FLAGS_FAN = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED_BRIGHTNESS
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_NATURAL_MODE
)

FEATURE_FLAGS_FAN_P5 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_NATURAL_MODE
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_LED
)

FEATURE_FLAGS_FAN_LESHOW_SS4 = FEATURE_SET_BUZZER
FEATURE_FLAGS_FAN_1C = FEATURE_FLAGS_FAN

FEATURE_FLAGS_FAN_ZA5 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED_BRIGHTNESS
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_NATURAL_MODE
    | FEATURE_SET_ANION
)

FEATURE_FLAGS_FAN_P33 = (
    FEATURE_SET_BUZZER
    | FEATURE_SET_CHILD_LOCK
    | FEATURE_SET_LED
    | FEATURE_SET_OSCILLATION_ANGLE
    | FEATURE_SET_NATURAL_MODE
)

FEATURE_FLAGS_FAN_P39 = (
    FEATURE_SET_CHILD_LOCK | FEATURE_SET_OSCILLATION_ANGLE | FEATURE_SET_NATURAL_MODE
)

SERVICE_SET_BUZZER_ON = "fan_set_buzzer_on"
SERVICE_SET_BUZZER_OFF = "fan_set_buzzer_off"
SERVICE_SET_CHILD_LOCK_ON = "fan_set_child_lock_on"
SERVICE_SET_CHILD_LOCK_OFF = "fan_set_child_lock_off"
SERVICE_SET_LED_BRIGHTNESS = "fan_set_led_brightness"
SERVICE_SET_RAW_LED_BRIGHTNESS = "fan_set_raw_led_brightness"
SERVICE_SET_OSCILLATION_ANGLE = "fan_set_oscillation_angle"
SERVICE_SET_DELAY_OFF = "fan_set_delay_off"
SERVICE_SET_NATURAL_MODE_ON = "fan_set_natural_mode_on"
SERVICE_SET_NATURAL_MODE_OFF = "fan_set_natural_mode_off"
SERVICE_SET_ANION_ON = "fan_set_anion_on"
SERVICE_SET_ANION_OFF = "fan_set_anion_off"

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=2))}
)

SERVICE_SCHEMA_RAW_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_BRIGHTNESS): vol.Coerce(int)}
)

SERVICE_SCHEMA_OSCILLATION_ANGLE = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_ANGLE): cv.positive_int}
)

SERVICE_SCHEMA_DELAY_OFF = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_DELAY_OFF_COUNTDOWN): cv.positive_int}
)

SERVICE_TO_METHOD = {
    SERVICE_SET_BUZZER_ON: {"method": "async_set_buzzer_on"},
    SERVICE_SET_BUZZER_OFF: {"method": "async_set_buzzer_off"},
    SERVICE_SET_CHILD_LOCK_ON: {"method": "async_set_child_lock_on"},
    SERVICE_SET_CHILD_LOCK_OFF: {"method": "async_set_child_lock_off"},
    SERVICE_SET_LED_BRIGHTNESS: {
        "method": "async_set_led_brightness",
        "schema": SERVICE_SCHEMA_LED_BRIGHTNESS,
    },
    SERVICE_SET_RAW_LED_BRIGHTNESS: {
        "method": "async_set_raw_led_brightness",
        "schema": SERVICE_SCHEMA_RAW_LED_BRIGHTNESS,
    },
    SERVICE_SET_OSCILLATION_ANGLE: {
        "method": "async_set_oscillation_angle",
        "schema": SERVICE_SCHEMA_OSCILLATION_ANGLE,
    },
    SERVICE_SET_DELAY_OFF: {
        "method": "async_set_delay_off",
        "schema": SERVICE_SCHEMA_DELAY_OFF,
    },
    SERVICE_SET_NATURAL_MODE_ON: {"method": "async_set_natural_mode_on"},
    SERVICE_SET_NATURAL_MODE_OFF: {"method": "async_set_natural_mode_off"},
    SERVICE_SET_ANION_ON: {"method": "async_set_anion_on"},
    SERVICE_SET_ANION_OFF: {"method": "async_set_anion_off"},
}


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the miio fan device from config."""
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config[CONF_HOST]
    token = config[CONF_TOKEN]
    name = config[CONF_NAME]
    model = config.get(CONF_MODEL)
    retries = config[CONF_RETRIES]
    preset_modes_override = config.get(CONF_PRESET_MODES_OVERRIDE)

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])
    unique_id = None

    if model is None:
        try:
            miio_device = Device(host, token)
            device_info = await hass.async_add_executor_job(miio_device.info)
            model = device_info.model
            unique_id = f"{model}-{device_info.mac_address}"
            _LOGGER.info(
                "%s %s %s detected",
                model,
                device_info.firmware_version,
                device_info.hardware_version,
            )
        except DeviceException as ex:
            raise PlatformNotReady from ex

    if model in [
        MODEL_FAN_V2,
        MODEL_FAN_V3,
        MODEL_FAN_SA1,
        MODEL_FAN_ZA1,
        MODEL_FAN_ZA3,
        MODEL_FAN_ZA4,
    ]:
        fan = Fan(host, token, model=model)
        device = XiaomiFan(name, fan, model, unique_id, retries, preset_modes_override)
    elif model == MODEL_FAN_P5:
        fan = FanP5(host, token, model=model)
        device = XiaomiFanP5(
            name, fan, model, unique_id, retries, preset_modes_override
        )
    elif model == MODEL_FAN_P9:
        fan = FanMiot(host, token, model=model)
        device = XiaomiFanMiot(
            name, fan, model, unique_id, retries, preset_modes_override
        )
    elif model in [MODEL_FAN_P10, MODEL_FAN_P18]:
        fan = FanMiot(host, token, model=MODEL_FAN_P10)
        device = XiaomiFanMiot(
            name, fan, model, unique_id, retries, preset_modes_override
        )
    elif model in [MODEL_FAN_P11, MODEL_FAN_P15]:
        fan = FanMiot(host, token, model=MODEL_FAN_P11)
        device = XiaomiFanMiot(
            name, fan, model, unique_id, retries, preset_modes_override
        )
    elif model == MODEL_FAN_LESHOW_SS4:
        fan = FanLeshow(host, token, model=model)
        device = XiaomiFanLeshow(
            name, fan, model, unique_id, retries, preset_modes_override
        )
    elif model in [MODEL_FAN_1C, MODEL_FAN_P8]:
        fan = Fan1C(host, token, model=model)
        device = XiaomiFan1C(
            name, fan, model, unique_id, retries, preset_modes_override
        )
    elif model == MODEL_FAN_ZA5:
        fan = FanZA5(host, token, model=model)
        device = XiaomiFanZA5(
            name, fan, model, unique_id, retries, preset_modes_override
        )
    elif model == MODEL_FAN_P33:
        fan = FanP33(host, token, model=model)
        device = XiaomiFanP33(
            name, fan, model, unique_id, retries, preset_modes_override
        )
    elif model == MODEL_FAN_P39:
        fan = FanP39(host, token, model=model)
        device = XiaomiFanP39(
            name, fan, model, unique_id, retries, preset_modes_override
        )
    else:
        _LOGGER.error(
            "Unsupported device found! Please create an issue at "
            "https://github.com/syssi/xiaomi_fan/issues "
            "and provide the following data: %s",
            model,
        )
        return False

    hass.data[DATA_KEY][host] = device
    async_add_entities([device], update_before_add=True)

    async def async_service_handler(service):
        """Map services to methods on XiaomiFan."""
        method = SERVICE_TO_METHOD.get(service.service)
        params = {
            key: value for key, value in service.data.items() if key != ATTR_ENTITY_ID
        }
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [
                device
                for device in hass.data[DATA_KEY].values()
                if device.entity_id in entity_ids
            ]
        else:
            devices = hass.data[DATA_KEY].values()

        update_tasks = []
        for device in devices:
            if not hasattr(device, method["method"]):
                continue
            await getattr(device, method["method"])(**params)
            update_tasks.append(asyncio.create_task(device.async_update_ha_state(True)))

        if update_tasks:
            await asyncio.wait(update_tasks)

    for air_purifier_service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[air_purifier_service].get(
            "schema", AIRPURIFIER_SERVICE_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, air_purifier_service, async_service_handler, schema=schema
        )


class XiaomiGenericDevice(FanEntity):
    """Representation of a generic Xiaomi device."""

    def __init__(self, name, device, model, unique_id, retries, preset_modes_override):
        """Initialize the generic Xiaomi device."""
        self._name = name
        self._device = device
        self._model = model
        self._unique_id = unique_id
        self._retry = 0
        self._retries = retries
        self._preset_modes_override = preset_modes_override

        self._available = False
        self._state = None
        self._state_attrs = {ATTR_MODEL: self._model}
        self._device_features = FEATURE_SET_BUZZER
        self._skip_update = False

    @property
    def supported_features(self):
        """Flag supported features."""
        return 0

    @property
    def should_poll(self):
        """Poll the device."""
        return True

    @property
    def unique_id(self):
        """Return an unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def available(self):
        """Return true when state is known."""
        return self._available

    @property
    def extra_state_attributes(self):
        """Return the extra state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @staticmethod
    def _extract_value_from_attribute(state, attribute):
        value = getattr(state, attribute, None)
        if isinstance(value, Enum):
            return value.value

        return value

    async def _try_command(self, mask_error, func, *args, **kwargs):
        """Call a miio device command handling error messages."""
        try:
            result = await self.hass.async_add_job(partial(func, *args, **kwargs))

            _LOGGER.debug("Response received from miio device: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            self._available = False
            return False

    async def async_turn_on(self, speed: str = None, **kwargs) -> None:
        """Turn the device on."""
        result = await self._try_command(
            "Turning the miio device on failed.", self._device.on
        )
        if speed:
            result = await self.async_set_speed(speed)

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        result = await self._try_command(
            "Turning the miio device off failed.", self._device.off
        )

        if result:
            self._state = False
            self._skip_update = True

    async def async_set_buzzer_on(self):
        """Turn the buzzer on."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Turning the buzzer of the miio device on failed.",
            self._device.set_buzzer,
            True,
        )

    async def async_set_buzzer_off(self):
        """Turn the buzzer off."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Turning the buzzer of the miio device off failed.",
            self._device.set_buzzer,
            False,
        )

    async def async_set_child_lock_on(self):
        """Turn the child lock on."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device on failed.",
            self._device.set_child_lock,
            True,
        )

    async def async_set_child_lock_off(self):
        """Turn the child lock off."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device off failed.",
            self._device.set_child_lock,
            False,
        )


class XiaomiFan(XiaomiGenericDevice):
    """Representation of a Xiaomi Pedestal Fan."""

    def __init__(self, name, device, model, unique_id, retries, preset_modes_override):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries, preset_modes_override)

        self._device_features = FEATURE_FLAGS_FAN
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._natural_mode = False

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        """Supported features."""
        return (
            SUPPORT_SET_SPEED
            | SUPPORT_PRESET_MODE
            | SUPPORT_OSCILLATE
            | SUPPORT_DIRECTION
        )

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._oscillate = state.oscillate
            self._natural_mode = state.natural_speed != 0
            self._state = state.is_on

            if self._natural_mode:
                for preset_mode, range in FAN_PRESET_MODES.items():
                    if state.natural_speed in range:
                        self._preset_mode = preset_mode
                        self._percentage = state.natural_speed
                        break
            else:
                for preset_mode, range in FAN_PRESET_MODES.items():
                    if state.direct_speed in range:
                        self._preset_mode = preset_mode
                        self._percentage = state.direct_speed
                        break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self):
        """Return the current speed."""
        return self._percentage

    @property
    def preset_modes(self):
        """Get the list of available preset modes."""
        return self._preset_modes

    @property
    def preset_mode(self):
        """Get the current preset mode."""
        return self._preset_mode

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if preset_mode == SPEED_OFF:
            await self.async_turn_off()
            return

        if self._natural_mode:
            await self._try_command(
                "Setting fan speed of the miio device failed.",
                self._device.set_natural_speed,
                FAN_PRESET_MODE_VALUES[preset_mode],
            )
        else:
            await self._try_command(
                "Setting fan speed of the miio device failed.",
                self._device.set_direct_speed,
                FAN_PRESET_MODE_VALUES[preset_mode],
            )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if self._natural_mode:
            await self._try_command(
                "Setting fan speed percentage of the miio device failed.",
                self._device.set_natural_speed,
                percentage,
            )
        else:
            await self._try_command(
                "Setting fan speed percentage of the miio device failed.",
                self._device.set_direct_speed,
                percentage,
            )

    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        if direction == "forward":
            direction = "right"

        if direction == "reverse":
            direction = "left"

        if self._oscillate:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

        await self._try_command(
            "Setting move direction of the miio device failed.",
            self._device.set_rotate,
            FanMoveDirection(direction),
        )

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._oscillate

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.set_oscillate,
                True,
            )
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

    async def async_set_oscillation_angle(self, angle: int) -> None:
        """Set oscillation angle."""
        if self._device_features & FEATURE_SET_OSCILLATION_ANGLE == 0:
            return

        await self._try_command(
            "Setting angle of the miio device failed.", self._device.set_angle, angle
        )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""

        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown * 60,
        )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_led_brightness,
            FanLedBrightness(brightness),
        )

    async def async_set_natural_mode_on(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        self._natural_mode = True
        await self.async_set_percentage(self._percentage)

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        self._natural_mode = False
        await self.async_set_percentage(self._percentage)


class XiaomiFanP5(XiaomiFan):
    """Representation of a Xiaomi Pedestal Fan P5."""

    def __init__(self, name, device, model, unique_id, retries, preset_modes_override):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries, preset_modes_override)

        self._device_features = FEATURE_FLAGS_FAN_P5
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P5
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._natural_mode = False

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.speed
            self._oscillate = state.oscillate
            self._natural_mode = state.mode == FanOperationMode.Nature
            self._state = state.is_on

            for preset_mode, range in FAN_PRESET_MODES.items():
                if state.speed in range:
                    self._preset_mode = preset_mode
                    break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )

            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if preset_mode == SPEED_OFF:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting fan speed of the miio device failed.",
            self._device.set_speed,
            FAN_PRESET_MODE_VALUES_P5[preset_mode],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting fan speed percentage of the miio device failed.",
            self._device.set_speed,
            percentage,
        )

    async def async_set_natural_mode_on(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Turning on natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationMode.Nature,
        )

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Turning on natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationMode.Normal,
        )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""

        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown,
        )


class XiaomiFanMiot(XiaomiFanP5):
    """Representation of a Xiaomi Pedestal Fan P9, P10, P11, P18."""

    pass


class XiaomiFanLeshow(XiaomiGenericDevice):
    """Representation of a Xiaomi Fan Leshow SS4."""

    def __init__(self, name, device, model, unique_id, retries, preset_modes_override):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries, preset_modes_override)

        self._device_features = FEATURE_FLAGS_FAN_LESHOW_SS4
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_LESHOW_SS4
        self._percentage = None
        self._preset_modes = [mode.name for mode in FanLeshowOperationMode]
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override
        self._oscillate = None

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        """Supported features."""
        return SUPPORT_SET_SPEED | SUPPORT_PRESET_MODE | SUPPORT_OSCILLATE

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.speed
            self._oscillate = state.oscillate
            self._state = state.is_on

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self):
        """Return the current speed."""
        return self._percentage

    @property
    def preset_modes(self):
        """Get the list of available preset modes."""
        return self._preset_modes

    @property
    def preset_mode(self):
        """Get the current preset mode."""
        if self._state:
            return FanLeshowOperationMode(self._state_attrs[ATTR_MODE]).name

        return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_mode,
            FanLeshowOperationMode[preset_mode.title()],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        await self._try_command(
            "Setting fan speed percentage of the miio device failed.",
            self._device.set_speed,
            percentage,
        )

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._oscillate

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.set_oscillate,
                True,
            )
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""

        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown,
        )


class XiaomiFan1C(XiaomiFan):
    """Representation of a Xiaomi Fan 1C."""

    def __init__(self, name, device, model, unique_id, retries, preset_modes_override):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries, preset_modes_override)

        self._device_features = FEATURE_FLAGS_FAN_1C
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_1C
        self._preset_modes = list(FAN_PRESET_MODES_1C)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._oscillate = None

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        """Supported features."""
        return SUPPORT_SET_SPEED | SUPPORT_PRESET_MODE | SUPPORT_OSCILLATE

    async def async_update(self):
        """Fetch state from the device."""
        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._oscillate = state.oscillate
            self._state = state.is_on

            for preset_mode, value in FAN_PRESET_MODES_1C.items():
                if state.speed == value:
                    self._preset_mode = preset_mode

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self) -> Optional[int]:
        """Return the current speed percentage."""
        return ordered_list_item_to_percentage(FAN_SPEEDS_1C, self._preset_mode)

    @property
    def speed_count(self) -> int:
        """Return the number of speeds the fan supports."""
        return len(FAN_SPEEDS_1C)

    @property
    def preset_modes(self):
        """Get the list of available preset modes."""
        return self._preset_modes

    @property
    def preset_mode(self):
        """Get the current preset mode."""
        if self._state:
            return self._preset_mode

        return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_speed,
            FAN_PRESET_MODES_1C[preset_mode],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_speed,
            FAN_PRESET_MODES_1C[
                percentage_to_ordered_list_item(FAN_SPEEDS_1C, percentage)
            ],
        )

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._oscillate

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.set_oscillate,
                True,
            )
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""

        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown,
        )

    async def async_set_natural_mode_on(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationMode.Nature,
        )

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationMode.Normal,
        )


class XiaomiFanZA5(XiaomiFan):
    """Representation of a Xiaomi Fan ZA5."""

    def __init__(self, name, device, model, unique_id, retries, preset_modes_override):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries, preset_modes_override)

        self._device_features = FEATURE_FLAGS_FAN_ZA5
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_ZA5
        self._preset_modes = list(FAN_PRESET_MODES_ZA5)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        return (
            SUPPORT_DIRECTION
            | SUPPORT_OSCILLATE
            | SUPPORT_PRESET_MODE
            | SUPPORT_SET_SPEED
        )

    async def async_update(self):
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.fan_speed
            self._oscillate = state.swing_mode
            self._natural_mode = state.mode == FanOperationMode.Nature
            self._state = state.power

            for preset_mode, value in FAN_PRESET_MODES_ZA5.items():
                if state.fan_level == value:
                    self._preset_mode = preset_mode

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                    if hasattr(state, value)
                }
            )
            self._retry = 0
        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self) -> Optional[int]:
        return self._percentage

    @property
    def speed_count(self) -> int:
        return 100

    @property
    def preset_modes(self):
        return self._preset_modes

    @property
    def preset_mode(self):
        if self._state:
            return self._preset_mode
        return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_speed,
            FAN_PRESET_MODE_VALUES[preset_mode],
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the speed percentage of the fan."""
        _LOGGER.debug("Setting the fan speed percentage to: %s", percentage)

        if percentage == 0:
            await self.async_turn_off()
            return

        if not self._state:
            await self._try_command(
                "Turning the miio device on failed.", self._device.on
            )
        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_speed,
            percentage,
        )

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.set_oscillate,
                True,
            )
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate,
                False,
            )

    async def async_set_delay_off(self, delay_off_countdown: int) -> None:
        """Set scheduled off timer in minutes."""

        await self._try_command(
            "Setting delay off miio device failed.",
            self._device.delay_off,
            delay_off_countdown * 60,
        )

    async def async_set_natural_mode_on(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationMode.Nature,
        )

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationMode.Normal,
        )

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        brightness = FanLedBrightness(brightness)
        if brightness == FanLedBrightness.Bright:
            brightness = 100
        elif brightness == FanLedBrightness.Dim:
            brightness = 1
        else:
            brightness = 0
        await self.async_set_raw_led_brightness(brightness)

    async def async_set_raw_led_brightness(self, brightness: int):
        """Set the raw led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_light,
            brightness,
        )

    async def async_set_anion_on(self):
        """Turn anion on."""
        if self._device_features & FEATURE_SET_ANION == 0:
            return

        await self._try_command(
            "Setting anion of the miio device failed.",
            self._device.set_anion,
            True,
        )

    async def async_set_anion_off(self):
        """Turn anion off."""
        if self._device_features & FEATURE_SET_ANION == 0:
            return

        await self._try_command(
            "Setting anion of the miio device failed.",
            self._device.set_anion,
            False,
        )


class OperationModeFanZA5(Enum):
    Nature = 0
    Normal = 1


class FanStatusZA5(DeviceStatus):
    """Container for status reports for FanZA5."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data

    # TODO: Docstrings.
    @property
    def anion(self) -> bool:
        return self.data["anion"]

    @property
    def battery_supported(self) -> bool:
        return self.data["battery_supported"]

    @property
    def buttons_pressed(self) -> str:
        code = self.data["buttons_pressed"]
        if code == 0:
            return "None"
        if code == 1:
            return "Power"
        if code == 2:
            return "Swing"
        return "Unknown"

    @property
    def buzzer(self) -> bool:
        return self.data["buzzer"]

    @property
    def child_lock(self) -> bool:
        return self.data["child_lock"]

    @property
    def fan_level(self) -> int:
        return self.data["fan_level"]

    @property
    def fan_speed(self) -> int:
        return self.data["fan_speed"]

    @property
    def humidity(self) -> int:
        return self.data["humidity"]

    @property
    def light(self) -> int:
        return self.data["light"]

    @property
    def light_enum(self) -> str:
        if self.light == 1:
            brightness = 1
        elif self.light == 0:
            brightness = 2
        else:
            brightness = 0
        return FanLedBrightness(brightness).name

    @property
    def mode(self) -> str:
        return OperationModeFanZA5(self.data["mode"]).name

    @property
    def power(self) -> bool:
        return self.data["power"]

    @property
    def power_off_time(self) -> int:
        return self.data["power_off_time"]

    @property
    def powersupply_attached(self) -> bool:
        return self.data["powersupply_attached"]

    @property
    def speed_rpm(self) -> int:
        return self.data["speed_rpm"]

    @property
    def swing_mode(self) -> bool:
        return self.data["swing_mode"]

    @property
    def swing_mode_angle(self) -> int:
        return self.data["swing_mode_angle"]

    @property
    def temperature(self) -> Any:
        return self.data["temperature"]

    @property
    def led(self) -> Optional[bool]:
        if self.light is None:
            return
        return self.light > 0

    @property
    def battery_state(self) -> str:
        if self.powersupply_attached:
            return "Charging"
        return "Discharging"


class FanZA5(MiotDevice):
    mapping = {
        # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:fan:0000A005:zhimi-za5:1
        "power": {"siid": 2, "piid": 1},
        "fan_level": {"siid": 2, "piid": 2},
        "swing_mode": {"siid": 2, "piid": 3},
        "swing_mode_angle": {"siid": 2, "piid": 5},
        "mode": {"siid": 2, "piid": 7},
        "power_off_time": {"siid": 2, "piid": 10},
        "anion": {"siid": 2, "piid": 11},
        "child_lock": {"siid": 3, "piid": 1},
        "light": {"siid": 4, "piid": 3},
        "buzzer": {"siid": 5, "piid": 1},
        "buttons_pressed": {"siid": 6, "piid": 1},
        "battery_supported": {"siid": 6, "piid": 2},
        "set_move": {"siid": 6, "piid": 3},
        "speed_rpm": {"siid": 6, "piid": 4},
        "powersupply_attached": {"siid": 6, "piid": 5},
        "fan_speed": {"siid": 6, "piid": 8},
        "humidity": {"siid": 7, "piid": 1},
        "temperature": {"siid": 7, "piid": 7},
    }

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = MODEL_FAN_ZA5,
    ) -> None:
        super().__init__(ip, token, start_id, debug, lazy_discover, model=model)

    def status(self):
        """Retrieve properties."""
        return FanStatusZA5(
            {
                prop["did"]: prop["value"] if prop["code"] == 0 else None
                for prop in self.get_properties_for_mapping()
            }
        )

    def on(self):
        """Power on."""
        return self.set_property("power", True)

    def off(self):
        """Power off."""
        return self.set_property("power", False)

    def set_anion(self, anion: bool):
        """Set anion on/off."""
        return self.set_property("anion", anion)

    def set_speed(self, speed: int):
        """Set fan speed."""
        if speed < 0 or speed > 100:
            raise FanException("Invalid speed: %s" % speed)

        return self.set_property("fan_speed", speed)

    def set_angle(self, angle: int):
        """Set the oscillation angle."""
        if angle not in [30, 60, 90, 120]:
            raise FanException(
                "Unsupported angle. Supported values: "
                + ", ".join("{0}".format(i) for i in [30, 60, 90, 120])
            )

        return self.set_property("swing_mode_angle", angle)

    def set_oscillate(self, oscillate: bool):
        """Set oscillate on/off."""
        if oscillate:
            return self.set_property("swing_mode", True)
        else:
            return self.set_property("swing_mode", False)

    def set_buzzer(self, buzzer: bool):
        """Set buzzer on/off."""
        if buzzer:
            return self.set_property("buzzer", True)
        else:
            return self.set_property("buzzer", False)

    def set_child_lock(self, lock: bool):
        """Set child lock on/off."""
        return self.set_property("child_lock", lock)

    def set_light(self, light: int):
        """Set indicator brightness."""
        if light < 0 or light > 100:
            raise FanException("Invalid light: %s" % light)

        return self.set_property("light", light)

    def set_mode(self, mode: FanOperationMode):
        """Set mode."""
        return self.set_property("mode", OperationModeFanZA5[mode.name].value)

    def delay_off(self, seconds: int):
        """Set delay off seconds."""

        if seconds < 0 or seconds > 10 * 60 * 60:
            raise FanException("Invalid value for a delayed turn off: %s" % seconds)

        return self.set_property("power_off_time", seconds)

    def set_rotate(self, direction: FanMoveDirection):
        """Rotate fan 7.5 degrees horizontally to given direction."""
        return self.set_property("set_move", direction.name.lower())


class XiaomiFanP33(XiaomiFanMiot):
    """Representation of a Xiaomi Fan P33."""

    def __init__(self, name, device, model, unique_id, retries, preset_modes_override):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries, preset_modes_override)

        self._device_features = FEATURE_FLAGS_FAN_P33
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P33
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES_P33)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._natural_mode = False

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        return (
            SUPPORT_DIRECTION
            | SUPPORT_OSCILLATE
            | SUPPORT_PRESET_MODE
            | SUPPORT_SET_SPEED
        )

    """
    TODO:
    - fan.turn_on works, but doesn't go to the declared percentage. This is
      not an issue when using set_percentage()
    - setting child lock works, but HA always reads the value as null
    """

    async def async_update(self):
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.fan_speed
            self._oscillate = state.oscillate
            self._natural_mode = state.mode == OperationModeFanP33.Nature
            self._state = state.power

            for preset_mode, value in FAN_PRESET_MODES_P33.items():
                if state.fan_level == value:
                    self._preset_mode = preset_mode
                    break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                    if hasattr(state, value)
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self) -> Optional[int]:
        return self._percentage

    @property
    def speed_count(self) -> int:
        return len(FAN_SPEEDS_P33)

    @property
    def preset_modes(self):
        return self._preset_modes

    @property
    def preset_mode(self):
        if self._state:
            return self._preset_mode
        return None

    async def async_set_natural_mode_on(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            OperationModeFanP33.Nature,
        )

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            OperationModeFanP33.Normal,
        )


class OperationModeFanP33(Enum):
    Normal = 0
    Nature = 1


class FanStatusP33(DeviceStatus):
    """Container for status reports for FanP33."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Response of a Fan (dmaker.fan.p33, fw: 2.1.3):

        {'did': 'power', 'siid': 2, 'piid': 1, 'code': 0, 'value': True},
        {'did': 'fan_level', 'siid': 2, 'piid': 2, 'code': 0, 'value': 1},
        {'did': 'oscillate', 'siid': 2, 'piid': 4, 'code': 0, 'value': False},
        {'did': 'angle', 'siid': 2, 'piid': 5, 'code': 0, 'value': 120},
        {'did': 'mode', 'siid': 2, 'piid': 3, 'code': 0, 'value': 1},
        {'did': 'delay_off_countdown', 'siid': 3, 'piid': 1, 'code': 0, 'value': 0},
        {'did': 'child_lock', 'siid': 7, 'piid': 1, 'code': 0, 'value': False},
        {'did': 'light', 'siid': 4, 'piid': 1, 'code': 0, 'value': True},
        {'did': 'buzzer', 'siid': 5, 'piid': 1, 'code': 0, 'value': True},
        {'did': 'motor_control', 'siid': 6, 'piid': 1, 'code': -4003},
        {'did': 'speed', 'siid': 2, 'piid': 6, 'code': 0, 'value': 20},
        """
        self.data = data

    @property
    def buzzer(self) -> bool:
        return self.data["buzzer"]

    @property
    def child_lock(self) -> bool:
        return self.data["child_lock"]

    @property
    def fan_level(self) -> int:
        return self.data["fan_level"]

    @property
    def fan_speed(self) -> int:
        return self.data["speed"]

    @property
    def light(self) -> bool:
        return self.data["light"]

    @property
    def led(self) -> bool:
        return self.light

    @property
    def mode(self) -> str:
        return OperationModeFanP33(self.data["mode"]).name

    @property
    def power(self) -> bool:
        return self.data["power"]

    @property
    def delay_off_countdown(self) -> int:
        return self.data["delay_off_countdown"]

    @property
    def oscillate(self) -> bool:
        return self.data["oscillate"]

    @property
    def angle(self) -> int:
        return self.data["angle"]


class FanP33(MiotDevice):
    mapping = {
        # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:fan:0000A005:dmaker-p33:1
        "power": {"siid": 2, "piid": 1},
        "fan_level": {"siid": 2, "piid": 2},
        "oscillate": {"siid": 2, "piid": 4},
        "angle": {"siid": 2, "piid": 5},
        "mode": {"siid": 2, "piid": 3},
        "delay_off_countdown": {"siid": 3, "piid": 1},
        "child_lock": {"siid": 7, "piid": 1},
        "light": {"siid": 4, "piid": 1},
        "buzzer": {"siid": 5, "piid": 1},
        "motor_control": {"siid": 6, "piid": 1},
        "speed": {"siid": 2, "piid": 6},
    }

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = MODEL_FAN_P33,
    ) -> None:
        super().__init__(ip, token, start_id, debug, lazy_discover, model=model)

    def status(self):
        """Retrieve properties."""
        return FanStatusP33(
            {
                prop["did"]: prop["value"] if prop["code"] == 0 else None
                for prop in self.get_properties_for_mapping()
            }
        )

    def on(self):
        """Power on."""
        return self.set_property("power", True)

    def off(self):
        """Power off."""
        return self.set_property("power", False)

    def set_speed(self, speed: int):
        """Set fan speed."""
        if speed < 0 or speed > 100:
            raise FanException("Invalid speed: %s" % speed)

        return self.set_property("speed", speed)

    def set_angle(self, angle: int):
        """Set the oscillation angle."""
        if angle not in [30, 60, 90, 120, 140]:
            raise FanException(
                "Unsupported angle. Supported values: "
                + ", ".join("{0}".format(i) for i in [30, 60, 90, 120, 140])
            )

        return self.set_property("angle", angle)

    def set_oscillate(self, oscillate: bool):
        """Set oscillate on/off."""
        if oscillate:
            return self.set_property("oscillate", True)
        else:
            return self.set_property("oscillate", False)

    def set_buzzer(self, buzzer: bool):
        """Set buzzer on/off."""
        if buzzer:
            return self.set_property("buzzer", True)
        else:
            return self.set_property("buzzer", False)

    def set_child_lock(self, lock: bool):
        """Set child lock on/off."""
        self.status()
        return self.set_property("child_lock", lock)

    def set_light(self, light: bool):
        """Set indicator state."""
        return self.set_property("light", light)

    def set_mode(self, mode: OperationModeFanP33):
        """Set mode."""
        return self.set_property("mode", OperationModeFanP33[mode.name].value)

    def delay_off(self, minutes: int):
        """Set delay off minutes."""

        if minutes < 0 or minutes > 480:
            raise FanException("Invalid value for a delayed turn off: %s" % minutes)

        return self.set_property("delay_off_countdown", minutes)

    def set_rotate(self, direction: FanMoveDirection):
        """Rotate fan 7.5 degrees horizontally to given direction."""
        # Values for P33
        # { "value": 0, "description": "NONE" },
        # { "value": 1, "description": "LEFT" },
        # { "value": 2, "description": "RIGHT" }
        value = 0
        if direction == FanMoveDirection.Left:
            value = 1
        elif direction == FanMoveDirection.Right:
            value = 2
        return self.set_property("motor_control", value)


class XiaomiFanP39(XiaomiFanMiot):
    """Representation of a Xiaomi Fan P39."""

    def __init__(self, name, device, model, unique_id, retries, preset_modes_override):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries, preset_modes_override)

        self._device_features = FEATURE_FLAGS_FAN_P39
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P39
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES_P39)
        if preset_modes_override is not None:
            self._preset_modes = preset_modes_override

        self._preset_mode = None
        self._oscillate = None
        self._natural_mode = False

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        return (
            SUPPORT_DIRECTION
            | SUPPORT_OSCILLATE
            | SUPPORT_PRESET_MODE
            | SUPPORT_SET_SPEED
        )

    async def async_update(self):
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._percentage = state.fan_speed
            self._oscillate = state.oscillate
            self._natural_mode = state.mode == OperationModeFanP39.Nature
            self._state = state.power

            for preset_mode, value in FAN_PRESET_MODES_P39.items():
                if state.fan_level == value:
                    self._preset_mode = preset_mode
                    break

            self._state_attrs.update(
                {
                    key: self._extract_value_from_attribute(state, value)
                    for key, value in self._available_attributes.items()
                    if hasattr(state, value)
                }
            )
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "%s Got exception while fetching the state: %s , _retry=%s",
                    self.__class__.__name__,
                    ex,
                    self._retry,
                )

    @property
    def percentage(self) -> Optional[int]:
        return self._percentage

    @property
    def speed_count(self) -> int:
        return len(FAN_SPEEDS_P39)

    @property
    def preset_modes(self):
        return self._preset_modes

    @property
    def preset_mode(self):
        if self._state:
            return self._preset_mode
        return None

    async def async_set_natural_mode_on(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            OperationModeFanP39.Nature,
        )

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            OperationModeFanP39.Normal,
        )


class OperationModeFanP39(Enum):
    Normal = 0
    Nature = 1
    Sleep = 2


class FanStatusP39(DeviceStatus):
    """Container for status reports for FanP39."""

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data

    @property
    def child_lock(self) -> bool:
        return self.data["child_lock"]

    @property
    def fan_level(self) -> int:
        return self.data["fan_level"]

    @property
    def fan_speed(self) -> int:
        return self.data["speed"]

    @property
    def mode(self) -> str:
        return OperationModeFanP39(self.data["mode"]).name

    @property
    def power(self) -> bool:
        return self.data["power"]

    @property
    def delay_off_countdown(self) -> int:
        return self.data["delay_off_countdown"]

    @property
    def oscillate(self) -> bool:
        return self.data["oscillate"]

    @property
    def angle(self) -> int:
        return self.data["angle"]


class FanP39(MiotDevice):
    mapping = {
        # https://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:fan:0000A005:dmaker-p39:1
        "power": {"siid": 2, "piid": 1},
        "fan_level": {"siid": 2, "piid": 2},
        "mode": {"siid": 2, "piid": 4},
        "oscillate": {"siid": 2, "piid": 5},
        "angle": {"siid": 2, "piid": 6},
        "delay_off_countdown": {"siid": 2, "piid": 8},
        "speed": {"siid": 2, "piid": 11},
        "child_lock": {"siid": 3, "piid": 1},
    }

    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = MODEL_FAN_P39,
    ) -> None:
        super().__init__(ip, token, start_id, debug, lazy_discover, model=model)

    def status(self):
        """Retrieve properties."""
        return FanStatusP39(
            {
                prop["did"]: prop["value"] if prop["code"] == 0 else None
                for prop in self.get_properties_for_mapping()
            }
        )

    def on(self):
        """Power on."""
        return self.set_property("power", True)

    def off(self):
        """Power off."""
        return self.set_property("power", False)

    def set_speed(self, speed: int):
        """Set fan speed."""
        if speed < 0 or speed > 100:
            raise FanException("Invalid speed: %s" % speed)

        return self.set_property("speed", speed)

    def set_angle(self, angle: int):
        """Set the oscillation angle."""
        if angle not in [30, 60, 90, 120, 140]:
            raise FanException(
                "Unsupported angle. Supported values: "
                + ", ".join("{0}".format(i) for i in [30, 60, 90, 120, 140])
            )

        return self.set_property("angle", angle)

    def set_oscillate(self, oscillate: bool):
        """Set oscillate on/off."""
        if oscillate:
            return self.set_property("oscillate", True)
        else:
            return self.set_property("oscillate", False)

    def set_child_lock(self, lock: bool):
        """Set child lock on/off."""
        self.status()
        return self.set_property("child_lock", lock)

    def set_mode(self, mode: OperationModeFanP39):
        """Set mode."""
        return self.set_property("mode", OperationModeFanP39[mode.name].value)

    def delay_off(self, minutes: int):
        """Set delay off minutes."""

        if minutes < 0 or minutes > 480:
            raise FanException("Invalid value for a delayed turn off: %s" % minutes)

        return self.set_property("delay_off_countdown", minutes)

    def set_rotate(self, direction: FanMoveDirection):
        """Rotate fan 7.5 degrees horizontally to given direction."""
        # Values for P39
        # { "value": 0, "description": "None" },
        # { "value": 1, "description": "Left" },
        # { "value": 2, "description": "Right" }
        value = 0
        if direction == FanMoveDirection.Left:
            value = 1
        elif direction == FanMoveDirection.Right:
            value = 2
        return self.set_property("motor_control", value)
