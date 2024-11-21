from machine import I2C, Pin
import sys

if sys.implementation.name != "micropython":
    from typing import Literal

from bme680.bme680_base import BME680Base


class BME680(BME680Base):
    def __init__(self, i2c: I2C | None = None, dev_addr: int = 0x77):
        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = I2C(0, scl=Pin(9), sda=Pin(8))
        self._dev_addr = dev_addr
        self.configure()

    def _read_data(self, addr: int, size: int):
        return self._i2c.readfrom_mem(self._dev_addr, addr, size)

    def _write_data(self, addr: int, data: bytes):
        self._i2c.writeto_mem(self._dev_addr, addr, data)

    @staticmethod
    def _bytes_to_int(
        data: bytes,
        byteorder,  # type: Literal["little", "big"]
        signed: bool,
    ):
        if not signed:
            # unsigned の場合はそのまま int.from_bytes を使う
            return int.from_bytes(data, byteorder)
        else:
            if byteorder == "big":
                data = data[::-1]
            if (data[-1] & 0b1000_0000) == 0:
                # 最上位ビットが 0 の時は int.from_bytes をつかう
                return int.from_bytes(data, "little")
            else:
                # 最上位ビットが 1 の時は
                # ビット反転させてから int.from_bytes をつかう
                data = bytes([~e & 0xFF for e in data])
                return -int.from_bytes(data, "little") - 1

    def _read_int(
        self,
        addr: int,
        size: int,
        byteorder,  # type: Literal["little", "big"]
        signed: bool = False,
    ):
        return self._bytes_to_int(self._read_data(addr, size), byteorder, signed=signed)
