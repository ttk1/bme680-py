import time
import sys

if sys.implementation.name != "micropython":
    from typing import Literal


class BME680Base:
    def configure(self):
        # calibration parameters
        self._par_t1 = self._read_int(0xE9, 2, "little")
        self._par_t2 = self._read_int(0x8A, 2, "little", True)
        self._par_t3 = self._read_int(0x8C, 1, "little", True)

        self._par_p1 = self._read_int(0x8E, 2, "little")
        self._par_p2 = self._read_int(0x90, 2, "little", True)
        self._par_p3 = self._read_int(0x92, 1, "little", True)
        self._par_p4 = self._read_int(0x94, 2, "little", True)
        self._par_p5 = self._read_int(0x96, 2, "little", True)
        self._par_p6 = self._read_int(0x99, 1, "little", True)
        self._par_p7 = self._read_int(0x98, 1, "little", True)
        self._par_p8 = self._read_int(0x9C, 2, "little", True)
        self._par_p9 = self._read_int(0x9E, 2, "little", True)
        self._par_p10 = self._read_int(0xA0, 1, "little")

        self._par_h1 = self._read_int(0xE2, 2, "little") >> 4
        self._par_h2 = self._read_int(0xE1, 2, "big") >> 4
        self._par_h3 = self._read_int(0xE4, 1, "little", True)
        self._par_h4 = self._read_int(0xE5, 1, "little", True)
        self._par_h5 = self._read_int(0xE6, 1, "little", True)
        self._par_h6 = self._read_int(0xE7, 1, "little")
        self._par_h7 = self._read_int(0xE8, 1, "little", True)

        # self._par_g1 = self._read_int(0xED, 1, "little", True)
        # self._par_g2 = self._read_int(0xEB, 2, "little", True)
        # self._par_g3 = self._read_int(0xEE, 1, "little", True)

        # default config
        # IIR フィルタ係数を 15 (100) に設定
        self.set_config((0b000_100_0_0).to_bytes(1, "little"))

        # default ctrl_hum, ctrl_meas
        # オーバーサンプリングを x16 (101) に設定
        self.set_ctrl_hum((0b00000_101).to_bytes(1, "little"))
        self.set_ctrl_meas((0b101_101_01).to_bytes(1, "little"))

    def _read_data(self, addr: int, size: int):
        raise NotImplementedError()

    def _write_data(self, addr: int, data: bytes):
        raise NotImplementedError()

    def _read_int(
        self,
        addr: int,
        size: int,
        byteorder,  # type: Literal["little", "big"]
        signed: bool = False,
    ):
        raise NotImplementedError()

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
            time.sleep(0.01)
            meas_status_0 = self._read_int(0x1D, 1, "little")
            new_data_0 = (meas_status_0 & 0b1000_0000) > 0
            measuring = (meas_status_0 & 0b0010_0000) > 0
            if new_data_0 == True and measuring == False:
                break

        self.temp = self._read_temp()
        self.press = self._read_press()
        self.hum = self._read_hum()

    def _read_temp(self):
        temp_adc = self._read_int(0x22, 3, "big") >> 4

        # Floating point:
        var1 = (temp_adc / 16384 - self._par_t1 / 1024) * self._par_t2
        var2 = (
            (temp_adc / 131072 - self._par_t1 / 8192)
            * (temp_adc / 131072 - self._par_t1 / 8192)
            * self._par_t3
            * 16
        )
        t_fine = var1 + var2
        temp_comp = t_fine / 5120

        # Integer:
        # var1 = (temp_adc >> 3) - (self._par_t1 << 1)
        # var2 = (var1 * self._par_t2) >> 11
        # var3 = ((((var1 >> 1) * (var1 >> 1)) >> 12) * (self._par_t3 << 4)) >> 14
        # t_fine = var2 + var3
        # temp_comp = ((t_fine * 5) + 128) >> 8

        # 気圧、湿度のキャリブレーションのために t_fine, temp_comp を保持しておく
        self._t_fine = t_fine
        self._temp_comp = temp_comp

        return temp_comp

    def _read_press(self):
        press_adc = self._read_int(0x1F, 3, "big") >> 4

        # Floating point:
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

        # Integer:
        # var1 = (self._t_fine >> 1) - 64000
        # var2 = ((((var1 >> 2) * (var1 >> 2) >> 11)) * self._par_p6) >> 2
        # var2 = var2 + ((var1 * self._par_p5) << 1)
        # var2 = (var2 >> 2) + (self._par_p4 << 16)
        # var1 = (((((var1 >> 2) * (var1 >> 2)) >> 13) * (self._par_p3 << 5)) >> 3) + (
        #     (self._par_p2 * var1) >> 1
        # )
        # var1 = var1 >> 18
        # var1 = ((32768 + var1) * self._par_p1) >> 15
        # press_comp = 1048576 - press_adc
        # press_comp = (press_comp - (var2 >> 12)) * 3125
        # if press_comp >= (1 << 30):
        #     press_comp = (press_comp // var1) << 1
        # else:
        #     press_comp = (press_comp << 1) // var1
        # var1 = (self._par_p9 * (((press_comp >> 3) * (press_comp >> 3)) >> 13)) >> 12
        # var2 = ((press_comp >> 2) * self._par_p8) >> 13
        # var3 = (
        #     (press_comp >> 8) * (press_comp >> 8) * (press_comp >> 8) * self._par_p10
        # ) >> 17
        # press_comp = press_comp + ((var1 + var2 + var3 + (self._par_p7 << 7)) >> 4)

        return press_comp

    def _read_hum(self):
        hum_adc = self._read_int(0x25, 2, "big")

        # Floating point:
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

        # Integer:
        # var1 = (
        #     hum_adc
        #     - (self._par_h1 << 4)
        #     - (((self._temp_comp * self._par_h3) // 100) >> 1)
        # )
        # var2 = (
        #     self._par_h2
        #     * (
        #         ((self._temp_comp * self._par_h4) // 100)
        #         + (
        #             ((self._temp_comp * ((self._temp_comp * self._par_h5) // 100)) >> 6)
        #             // 100
        #         )
        #         + (1 << 14)
        #     )
        # ) >> 10
        # var3 = var1 * var2
        # var4 = ((self._par_h6 << 7) + (self._temp_comp * self._par_h7) // 100) >> 4
        # var5 = ((var3 >> 14) * (var3 >> 14)) >> 10
        # var6 = (var4 * var5) >> 1
        # hum_comp = (var3 + var6) >> 12
        # hum_comp = (((var3 + var6) >> 10) * 1000) >> 12

        return hum_comp
