# Xiaomi Mi Smart Pedestal Fan

This is a custom component for home assistant to integrate the Xiaomi Mi Smart Fan.

Please follow the instructions on [Retrieving the Access Token](https://www.home-assistant.io/components/vacuum.xiaomi_miio/#retrieving-the-access-token) to get the API token to use in the configuration.yaml file.

Credits: Thanks to [Rytilahti](https://github.com/rytilahti/python-miio) for all the work.

## Features

### Pedestal Fan

* Power (on, off)
* Speed levels (Level 1, Level 2, Level 3, Level 4)
* Oscillate (on, off)
* Oscillation angle (30, 60, 90, 120)
* Natural mode (on, off)
* Rotate by 5 degrees (left, right)
* Child lock (on, off)
* LED brightness (bright, dim, off)
* Attributes
  - model
  - temperature (zhimi.fan.v2 and v3 only)
  - humidity (zhimi.fan.v2 and v3 only)
  - led_brightness
  - buzzer
  - child_lock
  - natural_level
  - oscillate
  - delay_off_countdown
  - speed
  - direct_speed
  - natural_speed
  - angle
  - use_time
  - ac_power
  - battery (zhimi.fan.v2 and v3 only)
  - battery_charge (zhimi.fan.v2 & v3 only)
  - button_pressed (zhimi.fan.v2 & v3 only)
  - led (zhimi.fan.v2 only)
  - battery_state (zhimi.fan.v2 only)


## Install

You can install this custom component by adding this repository ([https://github.com/syssi/xiaomi_fan](https://github.com/syssi/xiaomi_fan/)) to [HACS](https://hacs.xyz/) in the settings menu of HACS first. You will find the custom component in the integration menu afterwards, look for 'Xiaomi Mi Smart Pedestal Fan Integration'. Alternatively, you can install it manually by copying the custom_component folder to your Home Assistant configuration folder.


## Setup

```yaml
# configuration.yaml

fan:
  - platform: xiaomi_miio_fan
    name: Xiaomi Smart Fan
    host: 192.168.130.71
    token: b7c4a758c251955d2c24b1d9e41ce47d
```

Configuration variables:
- **host** (*Required*): The IP of your fan.
- **token** (*Required*): The API token of your fan.
- **name** (*Optional*): The name of your fan.
- **model** (*Optional*): The model of your device. Valid values are `zhimi.fan.v2`, `zhimi.fan.v3`, `zhimi.fan.sa1`, `zhimi.fan.za1`, `zhimi.fan.za3`, `zhimi.fan.za4` and `dmaker.fan.p5`. This setting can be used to bypass the device model detection and is recommended if your device isn't always available.

## Platform services

#### Service `fan.set_speed`

Set the fan speed.

| Service data attribute    | Optional | Description                                                                |
|---------------------------|----------|----------------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific fan entity. Else targets all.                       |
| `speed`                   |       no | Fan speed. Valid values are `Level 1`, `Level 2`, `Level 3` and `Level 4` as well as a value between 0 and 100. |

#### Service `fan.oscillate`

Oscillates the fan.

| Service data attribute    | Optional | Description                                                           |
|---------------------------|----------|-----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific fan entity. Else targets all.                  |
| `oscillating`             |       no | Flag to turn on/off oscillation. Valid values are `True` and `False`. |

#### Service `fan.set_direction`

Rotates the fan 5 degrees to the left/right.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific fan entity. Else targets all.                 |
| `direction`               |       no | Rotate the fan 5 degrees. Valid values are `left` and `right`.       |

#### Service `fan.xiaomi_miio_set_oscillation_angle`

Set the oscillation angle. Supported values are 30, 60, 90 and 120 degrees.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |
| `angle`                   |       no | Angle in degrees. Valid values are `30`, `60`, `90` and `120`.       |

#### Service `fan.xiaomi_miio_set_natural_mode_on`

Turn the natural mode on.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `fan.xiaomi_miio_set_natural_mode_off`

Turn the natural mode off.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `fan.xiaomi_miio_set_buzzer_on`

Turn the buzzer on.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `fan.xiaomi_miio_set_buzzer_off`

Turn the buzzer off.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `fan.xiaomi_miio_set_child_lock_on`

Turn the child lock on.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `fan.xiaomi_miio_set_child_lock_off`

Turn the child lock off.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `fan.xiaomi_miio_set_led_brightness`

Set the led brightness. Supported values are 0 (Bright), 1 (Dim), 2 (Off).

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |
| `brightness`              |       no | Brightness, between 0 and 2.                                         |

