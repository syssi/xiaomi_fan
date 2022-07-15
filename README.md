# Xiaomi Mi Smart Pedestal Fan

![GitHub actions](https://github.com/syssi/xiaomi_fan/actions/workflows/ci.yaml/badge.svg)
![GitHub stars](https://img.shields.io/github/stars/syssi/xiaomi_fan)
![GitHub forks](https://img.shields.io/github/forks/syssi/xiaomi_fan)
![GitHub watchers](https://img.shields.io/github/watchers/syssi/xiaomi_fan)
[!["Buy Me A Coffee"](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://www.buymeacoffee.com/syssi)

This is a custom component for home assistant to integrate the Xiaomi Mi Smart Fan.

Please follow the instructions on [Retrieving the Access Token](https://www.home-assistant.io/integrations/xiaomi_miio/#xiaomi-cloud-tokens-extractor) to get the API token to use in the configuration.yaml file.

Credits: Thanks to [Rytilahti](https://github.com/rytilahti/python-miio) for all the work.

## Supported devices

| Name                    | Model                  | Model no. | Specs |
| ----------------------- | ---------------------- | --------- | ----- |
| Pedestal Fan Fan V2     | zhimi.fan.v2           | | |
| Pedestal Fan Fan V3     | zhimi.fan.v3           | | |
| Pedestal Fan Fan SA1    | zhimi.fan.sa1          | | |
| Pedestal Fan Fan ZA1    | zhimi.fan.za1          | | |
| Pedestal Fan Fan ZA3    | zhimi.fan.za3          | | |
| Pedestal Fan Fan ZA4    | zhimi.fan.za4          | ZLBPLDS04ZM | |
| Smartmi Standing Fan 3  | zhimi.fan.za5          | | |
| Pedestal Fan Fan 1C     | dmaker.fan.1c          | | |
| Pedestal Fan Fan P5     | dmaker.fan.p5          | | |
| Pedestal Fan Fan P8     | dmaker.fan.p8          | | |
| Pedestal Fan Fan P9     | dmaker.fan.p9          | | |
| Pedestal Fan Fan P10    | dmaker.fan.p10         | | |
| Mijia Pedestal Fan      | dmaker.fan.p11         | BPLDS03DM  | 2800mAh, 24W, <=58dB  |
| Smart Standing Fan 2 Pro| dmaker.fan.p33         | BPLDS03DM  | 2800mAh, 24W, <=58dB  |
| Pedestal Fan Fan P15    | dmaker.fan.p15         | | |
| Mi Smart Standing Fan 2 | dmaker.fan.p18         | BPLDS02DM  | AC, 15W, 30.2-55.8bB  |
| Rosou SS4 Ventilator    | leshow.fan.ss4         | | |



## Features

### Pedestal Fan

* Power (on, off)
* Preset modes (Level 1, Level 2, Level 3, Level 4)
* Speed percentage (0...100)
* Oscillate (on, off)
* Oscillation angle (30, 60, 90, 120, 140, 150)
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
  - anion (zhimi.fan.za5 only)


### Rosou SS4 Ventilator (leshow.fan.ss4)

* Power (on, off)
* Operation modes (manual, sleep, strong, natural)
* Preset modes (Level 1, Level 2, Level 3, Level 4)
* Speed percentage (0...100)
* Oscillate (on, off)
* Buzzer (on, off)
* Delayed turn off (minutes)

* Attributes
  - `model`
  - `mode`
  - `speed`
  - `buzzer`
  - `oscillate`
  - `delay_off_countdown`
  - `error_detected`


## Install

You can install this custom component via [HACS](https://hacs.xyz/). Search for for 'Xiaomi Mi Smart Pedestal Fan Integration' at the integration page of HACS. Alternatively, you can install it manually by copying the custom_component folder to your Home Assistant configuration folder.

As next step you have to setup the custom component at your `configuration.yaml`. This custom component doesn't provide a `config-flow` right now. A restart of Home Assistant is required afterwards.

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
- **model** (*Optional*): The model of your device. This setting can be used to bypass the device model detection and is recommended if your device isn't always available.
- **preset_modes_override** (*Optional*): Overrides the list of preset modes. Can be used to suppress the preset mode switches at homekit by passing an empty list (`preset_modes_override: []`).

## Platform services

#### Service `fan.set_percentage`

Set the fan speed percentage.

| Service data attribute    | Optional | Description                                                                |
|---------------------------|----------|----------------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific fan entity. Else targets all.                       |
| `percentage`              |       no | Percentage speed setting. Valid values are between 0 and 100.              |

#### Service `fan.set_preset_mode`

Set a preset mode.

| Service data attribute    | Optional | Description                                                                  |
|---------------------------|----------|------------------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific fan entity. Else targets all.                         |
| `preset_mode`             |       no | Preset mode. Valid values are `Level 1`, `Level 2`, `Level 3` and `Level 4`. |

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
| `direction`               |       no | Rotate the fan 5 degrees. Valid values are `left`/`reverse` and `right`/`forward`.       |

#### Service `xiaomi_miio_fan.fan_set_oscillation_angle`

Set the oscillation angle. Supported values are 30, 60, 90 and 120 degrees.

| Service data attribute    | Optional | Description                                                            |
|---------------------------|----------|------------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.           |
| `angle`                   |       no | Angle in degrees. Valid values are `30`, `60`, `90`, `120`, and `140`. |

#### Service `xiaomi_miio_fan.fan_set_delay_off`

Set the scheduled turn off time. Supported values are 0, 60, 120, 180, 240, 300, 360, 420, 480 minutes. When 0 is passed, delay_off is disabled.


| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |
| `delay_off_countdown`     |       no | Time in minutes. Valid values are `0`, `60`, `120`, `180`, `240`, `300`, `240`, `300`, `360`, `420`, `480` minutes. |

#### Service `xiaomi_miio_fan.fan_set_natural_mode_on`

Turn the natural mode on.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `xiaomi_miio_fan.fan_set_natural_mode_off`

Turn the natural mode off.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `xiaomi_miio_fan.fan_set_buzzer_on`

Turn the buzzer on.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `xiaomi_miio_fan.fan_set_buzzer_off`

Turn the buzzer off.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `xiaomi_miio_fan.fan_set_child_lock_on`

Turn the child lock on.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `xiaomi_miio_fan.fan_set_child_lock_off`

Turn the child lock off.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `xiaomi_miio_fan.fan_set_led_brightness`

Set the led brightness. Supported values are 0 (Bright), 1 (Dim), 2 (Off).

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |
| `brightness`              |       no | Brightness, between 0 and 2.                                         |

#### Service `xiaomi_miio_fan.fan_set_anion_on`

Turn the ionizer on.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |

#### Service `xiaomi_miio_fan.fan_set_anion_off`

Turn the ionizer off.

| Service data attribute    | Optional | Description                                                          |
|---------------------------|----------|----------------------------------------------------------------------|
| `entity_id`               |      yes | Only act on a specific xiaomi miio entity. Else targets all.         |
