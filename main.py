#!/usr/bin/env python
from argparse import ArgumentParser
from asyncio import new_event_loop, sleep
from enum import Enum
from getpass import getpass
from logging import getLogger

from keyring import get_password, set_password
from plugp100.common.credentials import AuthCredential
from plugp100.new.device_factory import TapoBulb, connect, DeviceConnectConfiguration

logger = getLogger(__name__)

# local network configuration
bulbs = {
    "decke": [
        "192.168.0.87",
        "192.168.0.171",
        "192.168.0.52",
        "192.168.0.115"
    ],
    "bogenlampe": [
        "192.168.0.143"
    ]
}

class BulbAction(Enum):
    TURN_OFF = "off"
    TURN_ON = "on"
    TOGGLE = "toggle"

    def __str__(self):
        return self.value

async def connect_bulb(
        credentials: AuthCredential,
        host: str
        ) -> TapoBulb | None:
    device_configuration = DeviceConnectConfiguration(
        host=host,
        credentials=credentials,
        device_type="SMART.TAPOBULB",
        encryption_type="klap",
        encryption_version=2
    )
    device = await connect(device_configuration)
    await device.update()
    if isinstance(device, TapoBulb):
        return device
    else:
        logger.error("invalid device type")

async def main():
    parser = ArgumentParser()
    parser.add_argument("user_name", type=str)
    parser.add_argument("lamp_name", type=str)
    parser.add_argument("action", type=BulbAction, choices=list(BulbAction))
    prog_args = parser.parse_args()
    tapo_password = get_password("system", prog_args.user_name)
    if not tapo_password:
        tapo_password = getpass("please enter your password")
    credentials = AuthCredential(prog_args.user_name, tapo_password)
    if prog_args.lamp_name not in bulbs:
        logger.error("lamp name not defined")
        return
    bulb_names: list[str] = bulbs[prog_args.lamp_name]
    for bulb_name in bulb_names:
        device: TapoBulb | None = await connect_bulb(credentials, bulb_name)
        if not device:
            logger.error("skipping device, because not found")
            return
        if prog_args.action == BulbAction.TURN_ON:
            await device.turn_on()
        elif prog_args.action == BulbAction.TURN_OFF:
            await device.turn_off()
        elif prog_args.action == BulbAction.TOGGLE:
            if device.raw_state["device_on"]:
                await device.turn_off()
            else:
                await device.turn_on()
    set_password("system", prog_args.user_name, tapo_password)

if __name__ == "__main__":
    loop = new_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(sleep(0.1))
    loop.close()
