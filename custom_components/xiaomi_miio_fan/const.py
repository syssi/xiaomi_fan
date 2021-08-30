"""Constants of the Xiaomi/ZhiMi Smart Fan component."""

DEFAULT_NAME = "Xiaomi Miio Fan"
DEFAULT_RETRIES = 20
DATA_KEY = "fan.xiaomi_miio_fan"
DOMAIN = "xiaomi_miio_fan"
DOMAINS = ["fan"]

CONF_MODEL = "model"
CONF_RETRIES = "retries"
CONF_PRESET_MODES_OVERRIDE = "preset_modes_override"

MODEL_FAN_V2 = "zhimi.fan.v2"
MODEL_FAN_V3 = "zhimi.fan.v3"
MODEL_FAN_SA1 = "zhimi.fan.sa1"
MODEL_FAN_ZA1 = "zhimi.fan.za1"
MODEL_FAN_ZA3 = "zhimi.fan.za3"
MODEL_FAN_ZA4 = "zhimi.fan.za4"
MODEL_FAN_ZA5 = "zhimi.fan.za5"
MODEL_FAN_P5 = "dmaker.fan.p5"
MODEL_FAN_P8 = "dmaker.fan.p8"
MODEL_FAN_P9 = "dmaker.fan.p9"
MODEL_FAN_P10 = "dmaker.fan.p10"
MODEL_FAN_P11 = "dmaker.fan.p11"
MODEL_FAN_P15 = "dmaker.fan.p15"
MODEL_FAN_P18 = "dmaker.fan.p18"
MODEL_FAN_LESHOW_SS4 = "leshow.fan.ss4"
MODEL_FAN_1C = "dmaker.fan.1c"

AUTO_DETECT = "auto.detect"
OPT_MODEL = {
    AUTO_DETECT: "Auto Detect",
    MODEL_FAN_V2: "Pedestal Fan V2",
    MODEL_FAN_V3: "Pedestal Fan V3",
    MODEL_FAN_SA1: "Pedestal Fan SA1",
    MODEL_FAN_ZA1: "Pedestal Fan A1",
    MODEL_FAN_ZA3: "Pedestal Fan ZA3",
    MODEL_FAN_ZA4: "Pedestal Fan ZA4",
    MODEL_FAN_ZA5: "Pedestal Fan ZA5",
    MODEL_FAN_P5: "Pedestal Fan P5",
    MODEL_FAN_P8: "Pedestal Fan P8",
    MODEL_FAN_P9: "Pedestal Fan P9",
    MODEL_FAN_P10: "Pedestal Fan P10",
    MODEL_FAN_P11: "Pedestal Fan P11",
    MODEL_FAN_P15: "Pedestal Fan P15",
    MODEL_FAN_P18: "Pedestal Fan P18",
    MODEL_FAN_LESHOW_SS4: "Rosou SS4 Ventilator",
    MODEL_FAN_1C: "Pedestal Fan Fan 1C",
}

OPT_PRESET_MODE = {
    'Level 0': "Level 0",
    'Level 1': "Level 1",
    'Level 2': "Level 2",
    'Level 3': "Level 3",
    'Level 4': "Level 4"
}
