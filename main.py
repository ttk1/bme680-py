import os
import fcntl
import time

I2C_SLAVE = 0x0703

fd = os.open('/dev/i2c-1', os.O_RDWR)
# スレーブのアドレスを指定
fcntl.ioctl(fd, I2C_SLAVE, 0x77)


def show_temp():
    # 計測の実施
    os.write(fd, b'\x74' + b'\x91')

    # 計測が終わるまでちょっと待つ
    while True:
        time.sleep(0.1)
        os.write(fd, b'\x74')
        if os.read(fd, 1) != b'\x91':
            break

    # 計測結果の読み取り
    os.write(fd, b'\x22')
    temp_adc = int.from_bytes(os.read(fd, 3), 'big') >> 4

    os.write(fd, b'\xe9')
    par_t1 = int.from_bytes(os.read(fd, 2), 'little')

    os.write(fd, b'\x8a')
    par_t2 = int.from_bytes(os.read(fd, 2), 'little')

    os.write(fd, b'\x8c')
    par_t3 = int.from_bytes(os.read(fd, 1), 'little')

    # 温度の計測
    var1 = (temp_adc / 16384 - par_t1 / 1024) * par_t2
    var2 = ((temp_adc / 131072 - par_t1 / 8192) *
            (temp_adc / 131072 - par_t1 / 8192) * par_t3 * 16)
    t_fine = var1 + var2
    temp_comp = t_fine / 5120

    # 温度を表示
    print(temp_comp)


if __name__ == '__main__':
    while True:
        show_temp()
        time.sleep(1)
