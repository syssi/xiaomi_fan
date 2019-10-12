"""
Support for Xiaomi Mi Smart Pedestal Fan.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/fan.xiaomi_miio/
"""
import asyncio
from enum import Enum
from functools import partial
import logging

import voluptuous as vol

from homeassistant.components.fan import (FanEntity, PLATFORM_SCHEMA,
                                          SUPPORT_SET_SPEED, DOMAIN, SPEED_OFF,
                                          SUPPORT_OSCILLATE, SUPPORT_DIRECTION,
                                          ATTR_SPEED, ATTR_SPEED_LIST,
                                          ATTR_OSCILLATING, ATTR_DIRECTION, )
from homeassistant.const import (CONF_NAME, CONF_HOST, CONF_TOKEN,
                                 ATTR_ENTITY_ID, )
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Xiaomi Miio Fan'
DEFAULT_RETRIES = 20
DATA_KEY = 'fan.xiaomi_miio_fan'

CONF_MODEL = 'model'
CONF_RETRIES = 'retries'

MODEL_FAN_V2 = 'zhimi.fan.v2'
MODEL_FAN_V3 = 'zhimi.fan.v3'
MODEL_FAN_SA1 = 'zhimi.fan.sa1'
MODEL_FAN_ZA1 = 'zhimi.fan.za1'
MODEL_FAN_ZA3 = 'zhimi.fan.za3'
MODEL_FAN_ZA4 = 'zhimi.fan.za4'
MODEL_FAN_P5 = 'dmaker.fan.p5'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_TOKEN): vol.All(cv.string, vol.Length(min=32, max=32)),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_MODEL): vol.In([
        MODEL_FAN_V2,
        MODEL_FAN_V3,
        MODEL_FAN_SA1,
        MODEL_FAN_ZA1,
        MODEL_FAN_ZA3,
        MODEL_FAN_ZA4,
        MODEL_FAN_P5,
    ]),
    vol.Optional(CONF_RETRIES, default=DEFAULT_RETRIES): cv.positive_int,
})

ATTR_MODEL = 'model'
ATTR_BRIGHTNESS = 'brightness'

ATTR_TEMPERATURE = 'temperature'
ATTR_HUMIDITY = 'humidity'
ATTR_LED = 'led'
ATTR_LED_BRIGHTNESS = 'led_brightness'
ATTR_BUZZER = 'buzzer'
ATTR_CHILD_LOCK = 'child_lock'
ATTR_NATURAL_SPEED = 'natural_speed'
ATTR_OSCILLATE = 'oscillate'
ATTR_BATTERY = 'battery'
ATTR_BATTERY_CHARGE = 'battery_charge'
ATTR_BATTERY_STATE = 'battery_state'
ATTR_AC_POWER = 'ac_power'
ATTR_DELAY_OFF_COUNTDOWN = 'delay_off_countdown'
ATTR_ANGLE = 'angle'
ATTR_DIRECT_SPEED = 'direct_speed'
ATTR_USE_TIME = 'use_time'
ATTR_BUTTON_PRESSED = 'button_pressed'
ATTR_RAW_SPEED = 'raw_speed'
ATTR_MODE = 'mode'

AVAILABLE_ATTRIBUTES_FAN = {
    ATTR_ANGLE: 'angle',
    ATTR_RAW_SPEED: 'speed',
    ATTR_DELAY_OFF_COUNTDOWN: 'delay_off_countdown',

    ATTR_AC_POWER: 'ac_power',
    ATTR_OSCILLATE: 'oscillate',
    ATTR_DIRECT_SPEED: 'direct_speed',
    ATTR_NATURAL_SPEED: 'natural_speed',
    ATTR_CHILD_LOCK: 'child_lock',
    ATTR_BUZZER: 'buzzer',
    ATTR_LED_BRIGHTNESS: 'led_brightness',
    ATTR_USE_TIME: 'use_time',

    # Additional properties of version 2 and 3
    ATTR_TEMPERATURE: 'temperature',
    ATTR_HUMIDITY: 'humidity',
    ATTR_BATTERY: 'battery',
    ATTR_BATTERY_CHARGE: 'battery_charge',
    ATTR_BUTTON_PRESSED: 'button_pressed',

    # Additional properties of version 2
    ATTR_LED: 'led',
    ATTR_BATTERY_STATE: 'battery_state',
}

AVAILABLE_ATTRIBUTES_FAN_P5 = {
    ATTR_MODE: 'mode',
    ATTR_OSCILLATE: 'oscillate',
    ATTR_ANGLE: 'angle',
    ATTR_DELAY_OFF_COUNTDOWN: 'delay_off_countdown',
    ATTR_LED: 'led',
    ATTR_BUZZER: 'buzzer',
    ATTR_CHILD_LOCK: 'child_lock',
}

FAN_SPEED_LEVEL1 = 'Level 1'
FAN_SPEED_LEVEL2 = 'Level 2'
FAN_SPEED_LEVEL3 = 'Level 3'
FAN_SPEED_LEVEL4 = 'Level 4'

FAN_SPEED_LIST = {
    SPEED_OFF: range(0, 1),
    FAN_SPEED_LEVEL1: range(1, 26),
    FAN_SPEED_LEVEL2: range(26, 51),
    FAN_SPEED_LEVEL3: range(51, 76),
    FAN_SPEED_LEVEL4: range(76, 101)
}

FAN_SPEED_VALUES = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 45,
    FAN_SPEED_LEVEL3: 74,
    FAN_SPEED_LEVEL4: 100
}

FAN_SPEED_VALUES_P5 = {
    SPEED_OFF: 0,
    FAN_SPEED_LEVEL1: 1,
    FAN_SPEED_LEVEL2: 35,
    FAN_SPEED_LEVEL3: 70,
    FAN_SPEED_LEVEL4: 100
}

SUCCESS = ['ok']

FEATURE_SET_BUZZER = 1
FEATURE_SET_LED = 2
FEATURE_SET_CHILD_LOCK = 4
FEATURE_SET_LED_BRIGHTNESS = 8
FEATURE_SET_OSCILLATION_ANGLE = 16
FEATURE_SET_NATURAL_MODE = 32

FEATURE_FLAGS_GENERIC = (FEATURE_SET_BUZZER |
                         FEATURE_SET_CHILD_LOCK)

FEATURE_FLAGS_FAN = (FEATURE_FLAGS_GENERIC |
                     FEATURE_SET_LED_BRIGHTNESS |
                     FEATURE_SET_OSCILLATION_ANGLE |
                     FEATURE_SET_NATURAL_MODE)

FEATURE_FLAGS_FAN_P5 = (FEATURE_FLAGS_GENERIC |
                        FEATURE_SET_NATURAL_MODE |
                        FEATURE_SET_OSCILLATION_ANGLE |
                        FEATURE_SET_LED)

SERVICE_SET_BUZZER_ON = 'xiaomi_miio_set_buzzer_on'
SERVICE_SET_BUZZER_OFF = 'xiaomi_miio_set_buzzer_off'
SERVICE_SET_CHILD_LOCK_ON = 'xiaomi_miio_set_child_lock_on'
SERVICE_SET_CHILD_LOCK_OFF = 'xiaomi_miio_set_child_lock_off'
SERVICE_SET_LED_BRIGHTNESS = 'xiaomi_miio_set_led_brightness'
SERVICE_SET_OSCILLATION_ANGLE = 'xiaomi_miio_set_oscillation_angle'
SERVICE_SET_NATURAL_MODE_ON = 'xiaomi_miio_set_natural_mode_on'
SERVICE_SET_NATURAL_MODE_OFF = 'xiaomi_miio_set_natural_mode_off'

AIRPURIFIER_SERVICE_SCHEMA = vol.Schema({
    vol.Optional(ATTR_ENTITY_ID): cv.entity_ids,
})

SERVICE_SCHEMA_LED_BRIGHTNESS = AIRPURIFIER_SERVICE_SCHEMA.extend({
    vol.Required(ATTR_BRIGHTNESS):
        vol.All(vol.Coerce(int), vol.Clamp(min=0, max=2))
})

SERVICE_SCHEMA_OSCILLATION_ANGLE = AIRPURIFIER_SERVICE_SCHEMA.extend({
    vol.Required(ATTR_ANGLE):
        vol.All(vol.Coerce(int), vol.In([30, 60, 90, 120]))
})

SERVICE_TO_METHOD = {
    SERVICE_SET_BUZZER_ON: {'method': 'async_set_buzzer_on'},
    SERVICE_SET_BUZZER_OFF: {'method': 'async_set_buzzer_off'},
    SERVICE_SET_CHILD_LOCK_ON: {'method': 'async_set_child_lock_on'},
    SERVICE_SET_CHILD_LOCK_OFF: {'method': 'async_set_child_lock_off'},
    SERVICE_SET_LED_BRIGHTNESS: {
        'method': 'async_set_led_brightness',
        'schema': SERVICE_SCHEMA_LED_BRIGHTNESS},
    SERVICE_SET_OSCILLATION_ANGLE: {
        'method': 'async_set_oscillation_angle',
        'schema': SERVICE_SCHEMA_OSCILLATION_ANGLE},
    SERVICE_SET_NATURAL_MODE_ON: {'method': 'async_set_natural_mode_on'},
    SERVICE_SET_NATURAL_MODE_OFF: {'method': 'async_set_natural_mode_off'},
}


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_devices,
                               discovery_info=None):
    """Set up the miio fan device from config."""
    from miio import Device, DeviceException
    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = {}

    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)
    model = config.get(CONF_MODEL)
    retries = config.get(CONF_RETRIES)

    _LOGGER.info("Initializing with host %s (token %s...)", host, token[:5])
    unique_id = None

    if model is None:
        try:
            miio_device = Device(host, token)
            device_info = miio_device.info()
            model = device_info.model
            unique_id = "{}-{}".format(model, device_info.mac_address)
            _LOGGER.info("%s %s %s detected",
                         model,
                         device_info.firmware_version,
                         device_info.hardware_version)
        except DeviceException:
            raise PlatformNotReady

    if model in [MODEL_FAN_V2, MODEL_FAN_V3, MODEL_FAN_SA1, MODEL_FAN_ZA1,
                 MODEL_FAN_ZA3, MODEL_FAN_ZA4]:
        from miio import Fan
        fan = Fan(host, token, model=model)
        device = XiaomiFan(name, fan, model, unique_id)
    elif model == MODEL_FAN_P5:
        from miio import FanP5
        fan = FanP5(host, token, model=model)
        device = XiaomiFanP5(name, fan, model, unique_id)
    else:
        _LOGGER.error(
            'Unsupported device found! Please create an issue at '
            'https://github.com/syssi/xiaomi_fan/issues '
            'and provide the following data: %s', model)
        return False

    hass.data[DATA_KEY][host] = device
    async_add_devices([device], update_before_add=True)

    async def async_service_handler(service):
        """Map services to methods on XiaomiFan."""
        method = SERVICE_TO_METHOD.get(service.service)
        params = {key: value for key, value in service.data.items()
                  if key != ATTR_ENTITY_ID}
        entity_ids = service.data.get(ATTR_ENTITY_ID)
        if entity_ids:
            devices = [device for device in hass.data[DATA_KEY].values() if
                       device.entity_id in entity_ids]
        else:
            devices = hass.data[DATA_KEY].values()

        update_tasks = []
        for device in devices:
            if not hasattr(device, method['method']):
                continue
            await getattr(device, method['method'])(**params)
            update_tasks.append(device.async_update_ha_state(True))

        if update_tasks:
            await asyncio.wait(update_tasks, loop=hass.loop)

    for air_purifier_service in SERVICE_TO_METHOD:
        schema = SERVICE_TO_METHOD[air_purifier_service].get(
            'schema', AIRPURIFIER_SERVICE_SCHEMA)
        hass.services.async_register(
            DOMAIN, air_purifier_service, async_service_handler, schema=schema)


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
        self._state_attrs = {
            ATTR_MODEL: self._model,
        }
        self._device_features = FEATURE_FLAGS_GENERIC
        self._skip_update = False

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_SET_SPEED

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
        from miio import DeviceException
        try:
            result = await self.hass.async_add_job(
                partial(func, *args, **kwargs))

            _LOGGER.debug("Response received from miio device: %s", result)

            return result == SUCCESS
        except DeviceException as exc:
            _LOGGER.error(mask_error, exc)
            self._available = False
            return False

    async def async_turn_on(self, speed: str = None,
                            **kwargs) -> None:
        """Turn the device on."""
        result = await self._try_command("Turning the miio device on failed.", self._device.on)
        if speed:
            result = await self.async_set_speed(speed)        

        if result:
            self._state = True
            self._skip_update = True

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the device off."""
        result = await self._try_command(
            "Turning the miio device off failed.", self._device.off)

        if result:
            self._state = False
            self._skip_update = True

    async def async_set_buzzer_on(self):
        """Turn the buzzer on."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Turning the buzzer of the miio device on failed.",
            self._device.set_buzzer, True)

    async def async_set_buzzer_off(self):
        """Turn the buzzer off."""
        if self._device_features & FEATURE_SET_BUZZER == 0:
            return

        await self._try_command(
            "Turning the buzzer of the miio device off failed.",
            self._device.set_buzzer, False)

    async def async_set_child_lock_on(self):
        """Turn the child lock on."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device on failed.",
            self._device.set_child_lock, True)

    async def async_set_child_lock_off(self):
        """Turn the child lock off."""
        if self._device_features & FEATURE_SET_CHILD_LOCK == 0:
            return

        await self._try_command(
            "Turning the child lock of the miio device off failed.",
            self._device.set_child_lock, False)


class XiaomiFan(XiaomiGenericDevice):
    """Representation of a Xiaomi Pedestal Fan."""

    def __init__(self, name, device, model, unique_id, retries):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id, retries)

        self._device_features = FEATURE_FLAGS_FAN
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN
        self._speed_list = list(FAN_SPEED_LIST)
        self._speed = None
        self._oscillate = None
        self._natural_mode = False
        
        self._state_attrs[ATTR_SPEED] = None
        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes})

    @property
    def supported_features(self) -> int:
        """Supported features."""
        return SUPPORT_SET_SPEED | SUPPORT_OSCILLATE | SUPPORT_DIRECTION

    async def async_update(self):
        """Fetch state from the device."""
        from miio import DeviceException

        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._oscillate = state.oscillate
            self._natural_mode = (state.natural_speed != 0)
            self._state = state.is_on

            if self._natural_mode:
                for level, range in FAN_SPEED_LIST.items():
                    if state.natural_speed in range:
                        self._speed = level
                        self._state_attrs[ATTR_SPEED] = level
                        break
            else:
                for level, range in FAN_SPEED_LIST.items():
                    if state.direct_speed in range:
                        self._speed = level
                        self._state_attrs[ATTR_SPEED] = level
                        break

            self._state_attrs.update(
                {key: self._extract_value_from_attribute(state, value) for
                 key, value in self._available_attributes.items()})
            self._retry = 0

        except DeviceException as ex:
            self._retry = self._retry + 1
            if self._retry < self._retries:
                _LOGGER.info("Got exception while fetching the state: %s , _retry=%s", ex, self._retry)
            else:
                self._available = False
                _LOGGER.error("Got exception while fetching the state: %s , _retry=%s", ex, self._retry)

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return self._speed_list

    @property
    def speed(self):
        """Return the current speed."""
        return self._speed

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return

        _LOGGER.debug("Setting the fan speed to: %s", speed)

        if speed.isdigit():
            speed = int(speed)

        if speed in [SPEED_OFF, 0]:
            await self.async_turn_off()
            return

        # Map speed level to speed
        if speed in FAN_SPEED_VALUES:
            speed = FAN_SPEED_VALUES[speed]

        if self._natural_mode:
            await self._try_command(
                "Setting fan speed of the miio device failed.",
                self._device.set_natural_speed, speed)
        else:
            await self._try_command(
                "Setting fan speed of the miio device failed.",
                self._device.set_direct_speed, speed)

    async def async_set_direction(self, direction: str) -> None:
        """Set the direction of the fan."""
        from miio.fan import MoveDirection

        if direction in ['left', 'right']:
            if self._oscillate:
                await self._try_command(
                    "Setting oscillate off of the miio device failed.",
                    self._device.set_oscillate, False)

            await self._try_command(
                "Setting move direction of the miio device failed.",
                self._device.set_rotate, MoveDirection(direction))

    @property
    def oscillating(self):
        """Return the oscillation state."""
        return self._oscillate

    async def async_oscillate(self, oscillating: bool) -> None:
        """Set oscillation."""
        if oscillating:
            await self._try_command(
                "Setting oscillate on of the miio device failed.",
                self._device.set_oscillate, True)
        else:
            await self._try_command(
                "Setting oscillate off of the miio device failed.",
                self._device.set_oscillate, False)

    async def async_set_oscillation_angle(self, angle: int) -> None:
        """Set oscillation angle."""
        if self._device_features & FEATURE_SET_OSCILLATION_ANGLE == 0:
            return

        await self._try_command(
            "Setting angle of the miio device failed.",
            self._device.set_angle, angle)

    async def async_set_led_brightness(self, brightness: int = 2):
        """Set the led brightness."""
        if self._device_features & FEATURE_SET_LED_BRIGHTNESS == 0:
            return

        from miio.fan import LedBrightness

        await self._try_command(
            "Setting the led brightness of the miio device failed.",
            self._device.set_led_brightness, LedBrightness(brightness))

    async def async_set_natural_mode_on(self):
        """Turn the natural mode on."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        self._natural_mode = True
        await self.async_set_speed(self._speed)

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        self._natural_mode = False
        await self.async_set_speed(self._speed)


class XiaomiFanP5(XiaomiFan):
    """Representation of a Xiaomi Pedestal Fan P5."""

    def __init__(self, name, device, model, unique_id):
        """Initialize the fan entity."""
        super().__init__(name, device, model, unique_id)

        self._device_features = FEATURE_FLAGS_FAN
        self._available_attributes = AVAILABLE_ATTRIBUTES_FAN_P5
        self._speed_list = list(FAN_SPEED_LIST)
        self._speed = None
        self._oscillate = None
        self._natural_mode = False

        self._state_attrs[ATTR_SPEED] = None
        self._state_attrs.update(
            {attribute: None for attribute in self._available_attributes})

    async def async_update(self):
        """Fetch state from the device."""
        from miio import DeviceException
        from miio.fan import OperationMode

        # On state change the device doesn't provide the new state immediately.
        if self._skip_update:
            self._skip_update = False
            return

        try:
            state = await self.hass.async_add_job(self._device.status)
            _LOGGER.debug("Got new state: %s", state)

            self._available = True
            self._oscillate = state.oscillate
            self._natural_mode = (state.mode == OperationMode.Nature)
            self._state = state.is_on

            for level, range in FAN_SPEED_LIST.items():
                if state.speed in range:
                    self._speed = level
                    self._state_attrs[ATTR_SPEED] = level
                    break

            self._state_attrs.update(
                {key: self._extract_value_from_attribute(state, value) for
                 key, value in self._available_attributes.items()})

        except DeviceException as ex:
            self._available = False
            _LOGGER.error("Got exception while fetching the state: %s", ex)

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        if self.supported_features & SUPPORT_SET_SPEED == 0:
            return

        _LOGGER.debug("Setting the fan speed to: %s", speed)

        if speed.isdigit():
            speed = int(speed)

        if speed in [SPEED_OFF, 0]:
            await self.async_turn_off()
            return

        # Map speed level to speed
        if speed in FAN_SPEED_VALUES_P5:
            speed = FAN_SPEED_VALUES_P5[speed]

        await self._try_command(
            "Setting fan speed of the miio device failed.",
            self._device.set_speed,
            speed
        )

    async def async_set_natural_mode_on(self):
        """Turn the natural mode on."""
        from miio.fan import OperationMode

        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Turning on natural mode of the miio device failed.",
            self._device.set_mode,
            OperationMode.Nature
        )

    async def async_set_natural_mode_off(self):
        """Turn the natural mode off."""
        from miio.fan import OperationMode

        if self._device_features & FEATURE_SET_NATURAL_MODE == 0:
            return

        await self._try_command(
            "Turning on natural mode of the miio device failed.",
            self._device.set_mode,
            OperationMode.Normal
        )
