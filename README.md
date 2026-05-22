# Xiaomi Mi Smart Pedestal Fan (with P76 support)

This is a fork of [syssi/xiaomi_fan](https://github.com/syssi/xiaomi_fan) with added support for the **Xiaomi Smart Standing Air Circulation Fan (xiaomi.fan.p76)**, including vertical oscillation.

Credits: [syssi](https://github.com/syssi) for the original integration, [Rytilahti](https://github.com/rytilahti/python-miio) for python-miio.

## Supported devices

| Name                                        | Model                  | Model no.  | Specs |
| ------------------------------------------- | ---------------------- | ---------- | ----- |
| Pedestal Fan Fan V2                         | zhimi.fan.v2           | | |
| Pedestal Fan Fan V3                         | zhimi.fan.v3           | | |
| Pedestal Fan Fan SA1                        | zhimi.fan.sa1          | | |
| Pedestal Fan Fan ZA1                        | zhimi.fan.za1          | | |
| Pedestal Fan Fan ZA3                        | zhimi.fan.za3          | | |
| Pedestal Fan Fan ZA4                        | zhimi.fan.za4          | ZLBPLDS04ZM | |
| Smartmi Standing Fan 3                      | zhimi.fan.za5          | | |
| Pedestal Fan Fan 1C                         | dmaker.fan.1c          | | |
| Pedestal Fan Fan P5                         | dmaker.fan.p5          | | |
| Pedestal Fan Fan P8                         | dmaker.fan.p8          | | |
| Pedestal Fan Fan P9                         | dmaker.fan.p9          | | |
| Pedestal Fan Fan P10                        | dmaker.fan.p10         | | |
| Mijia Pedestal Fan                          | dmaker.fan.p11         | BPLDS03DM  | 2800mAh, 24W, <=58dB |
| Smart Standing Fan 2 Pro                    | dmaker.fan.p33         | BPLDS03DM  | 2800mAh, 24W, <=58dB |
| Pedestal Fan Fan P15                        | dmaker.fan.p15         | | |
| Mi Smart Standing Fan 2 P18                 | dmaker.fan.p18         | BPLDS02DM  | AC, 15W, 30.2-55.8dB |
| Mi Smart Standing Fan 2 P30                 | dmaker.fan.p30         | BPLDS02DM  | AC, 15W, 30.2-55.8dB |
| Rosou SS4 Ventilator                        | leshow.fan.ss4         | | |
| Xiaomi Smart Tower Fan                      | dmaker.fan.p39         | BPTS01DM   | 22W, <=63dB |
| **Xiaomi Smart Air Circulation Fan** *(new)*| **xiaomi.fan.p76**     | | MIoT, horizontal + vertical swing |


## Install via HACS

1. HACS → Integrations → ⋮ → **Custom repositories**
2. Add `https://github.com/b0x42/xiaomi_fan` — type: **Integration**
3. Install **"Xiaomi Mi Smart Pedestal Fan (with P76)"**
4. Restart Home Assistant

## Setup

```yaml
# configuration.yaml

fan:
  - platform: xiaomi_miio_fan_p76
    name: Xiaomi Fan P76
    host: 192.168.1.100
    token: YOUR_TOKEN_HERE
    model: xiaomi.fan.p76
```

Configuration variables:
- **host** (*Required*): IP address of the fan.
- **token** (*Required*): API token. See [Retrieving the Access Token](https://www.home-assistant.io/integrations/xiaomi_miio/#xiaomi-cloud-tokens-extractor).
- **name** (*Optional*): Entity name.
- **model** (*Optional*): Device model string. Recommended to set explicitly.
- **preset_modes_override** (*Optional*): Override preset mode list (e.g. `[]` to suppress HomeKit switches).


## P76-specific features

### Xiaomi Smart Air Circulation Fan (xiaomi.fan.p76)

* Power (on, off)
* Preset modes (Level 1–4) — gear-based (0-indexed device values)
* Speed percentage (1–100) — stepless
* Horizontal oscillation (on, off)
* Horizontal oscillation angle (30, 60, 90, 120°)
* Vertical oscillation (on, off) — *new service*
* Natural mode (on, off)
* Child lock (on, off)
* LED (on, off)
* Buzzer (on, off)
* Delayed turn off (0–480 minutes)

Attributes:
- `mode` — Straight / Natural
- `oscillate` — horizontal swing state
- `angle` — horizontal swing angle
- `vertical_oscillate` — vertical swing state
- `vertical_angle` — vertical swing angle
- `delay_off_countdown`
- `led`, `buzzer`, `child_lock`
- `raw_speed` — current stepless speed (1–100)


## Platform services

All service names use the domain `xiaomi_miio_fan_p76`.

#### `xiaomi_miio_fan_p76.fan_set_vertical_oscillation_on` / `_off`

Turn vertical oscillation on or off (P76 only).

| Attribute   | Optional | Description            |
|-------------|----------|------------------------|
| `entity_id` | yes      | Target fan entity.     |

#### `xiaomi_miio_fan_p76.fan_set_oscillation_angle`

| Attribute   | Optional | Description                                      |
|-------------|----------|--------------------------------------------------|
| `entity_id` | yes      | Target fan entity.                               |
| `angle`     | no       | Degrees: `30`, `60`, `90`, `120` (P76); `140` (others). |

#### `xiaomi_miio_fan_p76.fan_set_natural_mode_on` / `_off`

Toggle natural wind mode.

#### `xiaomi_miio_fan_p76.fan_set_delay_off`

| Attribute             | Optional | Description                                      |
|-----------------------|----------|--------------------------------------------------|
| `entity_id`           | yes      | Target fan entity.                               |
| `delay_off_countdown` | no       | Minutes: `0`, `60`, `120`, `180`, `240`, `300`, `360`, `420`, `480`. |

#### `xiaomi_miio_fan_p76.fan_set_buzzer_on` / `_off`
#### `xiaomi_miio_fan_p76.fan_set_child_lock_on` / `_off`
#### `xiaomi_miio_fan_p76.fan_set_led_brightness`

| Attribute    | Optional | Description                              |
|--------------|----------|------------------------------------------|
| `entity_id`  | yes      | Target fan entity.                       |
| `brightness` | no       | `0` = Bright, `1` = Dim, `2` = Off.     |
