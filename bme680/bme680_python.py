import os
import fcntl
import sys
from typing import Literal

from bme680.bme680_base import BME680Base

I2C_SLAVE = 0x0703


class BME680(BME680Base):
    def __init__(self, dev_file: str = "/dev/i2c-1", dev_addr: int = 0x77):
        self._fd = os.open(dev_file, os.O_RDWR)
        fcntl.ioctl(self._fd, I2C_SLAVE, dev_addr)
        self.configure()

    def _read_data(self, addr: int, size: int):
        os.write(self._fd, addr.to_bytes(1, "big"))
        return os.read(self._fd, size)

    def _write_data(self, addr: int, data: bytes):
        os.write(self._fd, addr.to_bytes(1, "big") + data)

    def _read_int(
        self,
        addr: int,
        size: int,
        byteorder: Literal["little", "big"],
        signed: bool = False,
    ):
        return int.from_bytes(self._read_data(addr, size), byteorder, signed=signed)
