"""
Support for Xiaomi Mi Smart Pedestal Fan.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/fan.xiaomi_miio/
"""
import asyncio
from enum import Enum
from functools import partial
import logging

from miio import (  # pylint: disable=import-error
    Device,
    DeviceException,
    Fan,
    FanLeshow,
    FanP5,
    Fan1C,
    FanP9,
    FanP10,
    FanP11,
)
from miio.fan import (  # pylint: disable=import-error, import-error
    LedBrightness as FanLedBrightness,
    MoveDirection as FanMoveDirection,
    OperationMode as FanOperationMode,
)
from miio.fan_leshow import (  # pylint: disable=import-error, import-error
    OperationMode as FanLeshowOperationMode,
)
from miio.fan_miot import (
    OperationModeMiot as FanOperationModeMiot
)
import voluptuous as vol

from homeassistant.components.fan import (
    ATTR_SPEED,
    PLATFORM_SCHEMA,
    SPEED_OFF,
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
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Xiaomi Miio Fan"
DEFAULT_RETRIES = 20
DATA_KEY = "fan.xiaomi_miio_fan"
DOMAIN = "xiaomi_miio_fan"

CONF_MODEL = "model"
CONF_RETRIES = "retries"

MODEL_FAN_V2 = "zhimi.fan.v2"
MODEL_FAN_V3 = "zhimi.fan.v3"
MODEL_FAN_SA1 = "zhimi.fan.sa1"
MODEL_FAN_ZA1 = "zhimi.fan.za1"
MODEL_FAN_ZA3 = "zhimi.fan.za3"
MODEL_FAN_ZA4 = "zhimi.fan.za4"
MODEL_FAN_P5 = "dmaker.fan.p5"
MODEL_FAN_P8 = "dmaker.fan.p8"
MODEL_FAN_P9 = "dmaker.fan.p9"
MODEL_FAN_P10 = "dmaker.fan.p10"
MODEL_FAN_P11 = "dmaker.fan.p11"
MODEL_FAN_LESHOW_SS4 = "leshow.fan.ss4"
MODEL_FAN_1C = "dmaker.fan.1c"

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
                MODEL_FAN_P5,
                MODEL_FAN_P8,
                MODEL_FAN_P9,
                MODEL_FAN_P10,
                MODEL_FAN_P11,
                MODEL_FAN_LESHOW_SS4,
                MODEL_FAN_1C,
            ]
        ),
        vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): cv.positive_int,
    }
)

ATTR_MODEL = "model"
ATTR_BRIGHTNESS = "brightness"

ATTR_TEMPERATURE = "temperature"
ATTR_HUMIDITY = "humidity"
ATTR_LED = "led"
ATTR_LED_BRIGHTNESS = "led_brightness"
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

SUCCESS = ["ok"]

FEATURE_SET_BUZZER = 1
FEATURE_SET_LED = 2
FEATURE_SET_CHILD_LOCK = 4
FEATURE_SET_LED_BRIGHTNESS = 8
FEATURE_SET_OSCILLATION_ANGLE = 16
FEATURE_SET_NATURAL_MODE = 32

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

SERVICE_SET_BUZZER_ON = "fan_set_buzzer_on"
SERVICE_SET_BUZZER_OFF = "fan_set_buzzer_off"
SERVICE_SET_CHILD_LOCK_ON = "fan_set_child_lock_on"
SERVICE_SET_CHILD_LOCK_OFF = "fan_set_child_lock_off"
SERVICE_SET_LED_BRIGHTNESS = "fan_set_led_brightness"
SERVICE_SET_OSCILLATION_ANGLE = "fan_set_oscillation_angle"
SERVICE_SET_DELAY_OFF = "fan_set_delay_off"
SERVICE_SET_NATURAL_MODE_ON = "fan_set_natural_mode_on"
SERVICE_SET_NATURAL_MODE_OFF = "fan_set_natural_mode_off"

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

SERVICE_SCHEMA_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Clamp(min=0, max=2))}
)

SERVICE_SCHEMA_OSCILLATION_ANGLE = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {vol.Required(ATTR_ANGLE): cv.positive_int}
)

SERVICE_SCHEMA_DELAY_OFF = AIRPURIFIER_SERVICE_SCHEMA.extend(
    {
        vol.Required(ATTR_DELAY_OFF_COUNTDOWN): vol.All(
            vol.Coerce(int), vol.In([0, 60, 120, 180, 240, 300, 360, 420, 480])
        )
    }
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
        device = XiaomiFan(name, fan, model, unique_id, retries)
    elif model == MODEL_FAN_P5:
        fan = FanP5(host, token, model=model)
        device = XiaomiFanP5(name, fan, model, unique_id, retries)
    elif model == MODEL_FAN_P9:
        fan = FanP9(host, token, model=model)
        device = XiaomiFanMiot(name, fan, model, unique_id, retries)
    elif model == MODEL_FAN_P10:
        fan = FanP10(host, token, model=model)
        device = XiaomiFanMiot(name, fan, model, unique_id, retries)
    elif model == MODEL_FAN_P11:
        fan = FanP11(host, token, model=model)
        device = XiaomiFanMiot(name, fan, model, unique_id, retries)
    elif model == MODEL_FAN_LESHOW_SS4:
        fan = FanLeshow(host, token, model=model)
        device = XiaomiFanLeshow(name, fan, model, unique_id, retries)
    elif model in [MODEL_FAN_1C, MODEL_FAN_P8]:
        fan = Fan1C(host, token, model=model)
        device = XiaomiFan1C(name, fan, model, unique_id, retries)
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
            update_tasks.append(device.async_update_ha_state(True))

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

    def __init__(self, name, device, model, unique_id, retries):
        """Initialize the generic Xiaomi device."""
        self._name = name
        self._device = device
        self._model = model
        self._unique_id = unique_id
        self._retry = 0
        self._retries = retries

        self._available = False
        self._state = None
        self._state_attrs = {ATTR_MODEL: self._model}
        self._device_features = FEATURE_SET_BUZZER
        self._skip_update = False

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_PRESET_MODE

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
    def device_state_attributes(self):
        """Return the state attributes of the device."""
        return self._state_attrs

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state

    @staticmethod
    def _extract_value_from_attribute(state, attribute):
        value = getattr(state, attribute)
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

    def __init__(self, name, device, model, unique_id, retries):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries)

        self._device_features = FEATURE_FLAGS_FAN
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES)
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
                    "Got exception while fetching the state: %s , _retry=%s",
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "Got exception while fetching the state: %s , _retry=%s",
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
        if direction == 'forward':
            direction = 'right'

        if direction == 'reverse':
            direction = 'left'

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

    def __init__(self, name, device, model, unique_id, retries):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries)

        self._device_features = FEATURE_FLAGS_FAN_P5
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P5
        self._percentage = None
        self._preset_modes = list(FAN_PRESET_MODES)
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
                    "Got exception while fetching the state: %s , _retry=%s",
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "Got exception while fetching the state: %s , _retry=%s",
                    ex,
                    self._retry,
                )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        _LOGGER.debug("Setting the preset mode to: %s", preset_mode)

        if preset_mode == SPEED_OFF:
            await self.async_turn_off()
            return

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
    """Representation of a Xiaomi Pedestal Fan P9, P10, P11."""


class XiaomiFanLeshow(XiaomiGenericDevice):
    """Representation of a Xiaomi Fan Leshow SS4."""

    def __init__(self, name, device, model, unique_id, retries):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries)

        self._device_features = FEATURE_FLAGS_FAN_LESHOW_SS4
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_LESHOW_SS4
        self._percentage = None
        self._preset_modes = [mode.name for mode in FanLeshowOperationMode]
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
                    "Got exception while fetching the state: %s , _retry=%s",
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "Got exception while fetching the state: %s , _retry=%s",
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

    def __init__(self, name, device, model, unique_id, retries):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries)

        self._device_features = FEATURE_FLAGS_FAN_1C
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_1C
        self._preset_modes = list(FAN_PRESET_MODES_1C)
        self._oscillate = None

        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes}
        )

    @property
    def supported_features(self) -> int:
        """Supported features."""
        return SUPPORT_PRESET_MODE | SUPPORT_OSCILLATE

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
                    "Got exception while fetching the state: %s , _retry=%s",
                    ex,
                    self._retry,
                )
            else:
                self._available = False
                _LOGGER.error(
                    "Got exception while fetching the state: %s , _retry=%s",
                    ex,
                    self._retry,
                )

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

        await self._try_command(
            "Setting preset mode of the miio device failed.",
            self._device.set_speed,
            FAN_PRESET_MODES_1C[preset_mode],
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
            FanOperationModeMiot.Nature,
        )

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Setting fan natural mode of the miio device failed.",
            self._device.set_mode,
            FanOperationModeMiot.Normal,
        )
