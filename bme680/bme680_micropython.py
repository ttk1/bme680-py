from machine import I2C, Pin
import utime

ENDIAN_LITTLE = "little"
ENDIAN_BIG = "big"


class BME680:
    def __init__(self, i2c: I2C | None = None, dev_addr: int = 0x77):
        if i2c is not None:
            self._i2c = i2c
        else:
            self._i2c = I2C(0, scl=Pin(9), sda=Pin(8))
        self._dev_addr = dev_addr

        # calibration parameters
        # 値が符号付きかどうかはここを参照:
        # https://github.com/boschsensortec/BME680_driver/blob/757e1f155c13bcdd34403579bd246b27f2963bf4/bme680.c#L719
        self._par_t1 = self._read_int(0xE9, 2, ENDIAN_LITTLE)
        self._par_t2 = self._read_int(0x8A, 2, ENDIAN_LITTLE, True)
        self._par_t3 = self._read_int(0x8C, 1, ENDIAN_LITTLE, True)

        self._par_p1 = self._read_int(0x8E, 2, ENDIAN_LITTLE)
        self._par_p2 = self._read_int(0x90, 2, ENDIAN_LITTLE, True)
        self._par_p3 = self._read_int(0x92, 1, ENDIAN_LITTLE, True)
        self._par_p4 = self._read_int(0x94, 2, ENDIAN_LITTLE, True)
        self._par_p5 = self._read_int(0x96, 2, ENDIAN_LITTLE, True)
        self._par_p6 = self._read_int(0x99, 1, ENDIAN_LITTLE, True)
        self._par_p7 = self._read_int(0x98, 1, ENDIAN_LITTLE, True)
        self._par_p8 = self._read_int(0x9C, 2, ENDIAN_LITTLE, True)
        self._par_p9 = self._read_int(0x9E, 2, ENDIAN_LITTLE, True)
        self._par_p10 = self._read_int(0xA0, 1, ENDIAN_LITTLE)

        self._par_h1 = self._read_int(0xE2, 2, ENDIAN_LITTLE) >> 4
        self._par_h2 = self._read_int(0xE1, 2, ENDIAN_BIG) >> 4
        self._par_h3 = self._read_int(0xE4, 1, ENDIAN_LITTLE, True)
        self._par_h4 = self._read_int(0xE5, 1, ENDIAN_LITTLE, True)
        self._par_h5 = self._read_int(0xE6, 1, ENDIAN_LITTLE, True)
        self._par_h6 = self._read_int(0xE7, 1, ENDIAN_LITTLE)
        self._par_h7 = self._read_int(0xE8, 1, ENDIAN_LITTLE, True)

        # default config
        # IIR フィルタ係数を 15 (100) に設定
        self.set_config((0b000_100_0_0).to_bytes(1, ENDIAN_LITTLE))

        # default ctrl_hum, ctrl_meas
        # オーバーサンプリングを x16 (101) に設定
        self.set_ctrl_hum((0b00000_101).to_bytes(1, ENDIAN_LITTLE))
        self.set_ctrl_meas((0b101_101_01).to_bytes(1, ENDIAN_LITTLE))

    def _read_data(self, addr: int, size: int):
        return self._i2c.readfrom_mem(self._dev_addr, addr, size)

    def _write_data(self, addr: int, data: bytes):
        self._i2c.writeto_mem(self._dev_addr, addr, data)

    @staticmethod
    def _bytes_to_int(data: bytes, byteorder, signed: bool):
        if not signed:
            # unsigned の場合はそのまま int.from_bytes を使う
            return int.from_bytes(data, byteorder)
        else:
            if byteorder == ENDIAN_BIG:
                data = data[::-1]
            if (data[-1] & 0b1000_0000) == 0:
                # 最上位ビットが 0 の時は int.from_bytes をつかう
                return int.from_bytes(data, ENDIAN_LITTLE)
            else:
                # 最上位ビットが 1 の時は
                # ビット反転させてから int.from_bytes をつかう
                data = bytes([~e & 0xFF for e in data])
                return -int.from_bytes(data, ENDIAN_LITTLE) - 1

    def _read_int(self, addr: int, size: int, byteorder: str, signed: bool = False):
        return self._bytes_to_int(self._read_data(addr, size), byteorder, signed=signed)

    def set_config(self, config: bytes):
        self._config = config

    def set_ctrl_hum(self, ctrl_hum: bytes):
        self._ctrl_hum = ctrl_hum

    def set_ctrl_meas(self, ctrl_meas: bytes):
        self._ctrl_meas = ctrl_meas

    def measure(self):
        # config
        self._write_data(0x75, self._config)

        # ctrl_hum
        self._write_data(0x72, self._ctrl_hum)

        # ctrl_meas
        self._write_data(0x74, self._ctrl_meas)

        # 計測が終わるまで待つ
        while True:
            utime.sleep(0.01)
            meas_status_0 = self._read_int(0x1D, 1, ENDIAN_LITTLE)
            new_data_0 = (meas_status_0 & 0b1000_0000) > 0
            measuring = (meas_status_0 & 0b0010_0000) > 0
            if new_data_0 == True and measuring == False:
                break
        self.temp = self._read_temp()
        self.press = self._read_press()
        self.hum = self._read_hum()

    def _read_temp(self):
        temp_adc = self._read_int(0x22, 3, ENDIAN_BIG) >> 4
        var1 = (temp_adc / 16384 - self._par_t1 / 1024) * self._par_t2
        var2 = (
            (temp_adc / 131072 - self._par_t1 / 8192)
            * (temp_adc / 131072 - self._par_t1 / 8192)
            * self._par_t3
            * 16
        )
        t_fine = var1 + var2
        temp_comp = t_fine / 5120

        # 気圧、湿度のキャリブレーションのために t_fine, temp_comp を保持しておく
        self._t_fine = t_fine
        self._temp_comp = temp_comp

        return temp_comp

    def _read_press(self):
        press_adc = self._read_int(0x1F, 3, ENDIAN_BIG) >> 4
        var1 = self._t_fine / 2 - 64000
        var2 = var1 * var1 * (self._par_p6 / 131072)
        var2 = var2 + var1 * self._par_p5 * 2
        var2 = var2 / 4 + self._par_p4 * 65536
        var1 = ((self._par_p3 * var1 * var1) / 16384 + self._par_p2 * var1) / 524188
        var1 = (1 + var1 / 32768) * self._par_p1
        press_comp = 1048576 - press_adc
        press_comp = ((press_comp - var2 / 4096) * 6250) / var1
        var1 = (self._par_p9 * press_comp * press_comp) / 2147483648
        var2 = press_comp * (self._par_p8 / 32768)
        var3 = (
            (press_comp / 256)
            * (press_comp / 256)
            * (press_comp / 256)
            * (self._par_p10 / 131072)
        )
        press_comp = press_comp + (var1 + var2 + var3 + self._par_p7 * 128) / 16
        return press_comp

    def _read_hum(self):
        hum_adc = self._read_int(0x25, 2, ENDIAN_BIG)
        var1 = hum_adc - (self._par_h1 * 16 + (self._par_h3 / 2) * self._temp_comp)
        var2 = (
            var1
            * (self._par_h2 / 262144)
            * (
                1.0
                + (self._par_h4 / 16384) * self._temp_comp
                + (self._par_h5 / 1048576) * self._temp_comp * self._temp_comp
            )
        )
        var3 = self._par_h6 / 16384
        var4 = self._par_h7 / 2097152
        hum_comp = var2 + (var3 + (var4 * self._temp_comp)) * var2 * var2
        return hum_comp
