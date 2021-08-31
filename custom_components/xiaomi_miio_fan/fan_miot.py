"""
Support for Xiaomi Mi Smart Pedestal Fan.

For more details about this platform, please refer to the documentation
https://home-assistant.io/components/fan.xiaomi_miio/
"""
import enum
from typing import Any, Dict

import click

from miio import (  # pylint: disable=import-error
    FanMiot
)
from miio.click_common import EnumType, command, format_output
from miio.fan_common import FanException, OperationMode
from miio.fan_miot import FanStatusMiot
from .const import MODEL_FAN_FA1
import logging
_LOGGER = logging.getLogger(__name__)


# http://miot-spec.org/miot-spec-v2/instance?type=urn:miot-spec-v2:device:fan:0000A005:zhimi-fa1:1
MIOT_MAPPING = {
    MODEL_FAN_FA1: {
        "power": {"siid": 2, "piid": 1},
        "fan_level": {"siid": 2, "piid": 2},
        "child_lock": {"siid": 6, "piid": 1},
        "fan_speed": {"siid": 5, "piid": 10},
        # Horizontal Swing
        "swing_mode": {"siid": 2, "piid": 3},
#        "direction": {"siid": 2, "piid": 4},
        # Horizontal Angle
        "swing_mode_angle": {"siid": 2, "piid": 5},
        "power_off_time": {"siid": 5, "piid": 2},
        "buzzer": {"siid": 2, "piid": 11},
        "light": {"siid": 2, "piid": 10},
        "mode": {"siid": 2, "piid": 7},
        # Vertical Swing
        "set_move": {"siid": 2, "piid": 4},
    }
}
SUPPORTED_ANGLES = {
    MODEL_FAN_FA1: [30, 60, 90, 120]
}


class OperationModeFanFA1(enum.Enum):
    Nature = 0
    Normal = 1


class FanStatusMiotFA1(FanStatusMiot):

    @property
    def mode(self) -> OperationMode:
        """Operation mode (normal or nature)."""
        return OperationMode[OperationModeFanFA1(self.data["mode"]).name]


class FanFA1(FanMiot):
    mapping = MIOT_MAPPING[MODEL_FAN_FA1]
    def __init__(
        self,
        ip: str = None,
        token: str = None,
        start_id: int = 0,
        debug: int = 0,
        lazy_discover: bool = True,
        model: str = MODEL_FAN_FA1,
    ) -> None:
        if model not in MIOT_MAPPING:
            raise FanException("Invalid FanFA1 model: %s" % model)

        super().__init__(ip, token, start_id, debug, lazy_discover)
        self.model = model

    @command(
        default_output=format_output(
            "",
            "Power: {result.power}\n"
            "Operation mode: {result.mode}\n"
            "Speed: {result.speed}\n"
            "Oscillate: {result.oscillate}\n"
            "Angle: {result.angle}\n"
            "LED: {result.led}\n"
            "Buzzer: {result.buzzer}\n"
            "Child lock: {result.child_lock}\n"
            "Power-off time: {result.delay_off_countdown}\n",
        )
    )
    def status(self) -> FanStatusMiotFA1:
        """Retrieve properties."""
        return FanStatusMiotFA1(
            {
                prop["did"]: prop["value"] if prop["code"] == 0 else None
                for prop in self.get_properties_for_mapping()
            }
        )

    @command(
        click.argument("angle", type=int),
        default_output=format_output("Setting angle to {angle}"),
    )
    def set_angle(self, angle: int):
        """Set the oscillation angle."""
        if angle not in SUPPORTED_ANGLES[self.model]:
            raise FanException(
                "Unsupported angle. Supported values: "
                + ", ".join("{0}".format(i) for i in SUPPORTED_ANGLES[self.model])
            )

        return self.set_property("swing_mode_angle", angle)
