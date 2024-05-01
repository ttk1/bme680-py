# bme680-py

BME680 のデータを Python で読むための何か

* 対象のセンサーモジュール: https://akizukidenshi.com/catalog/g/g114469/
* BME680 のデータシート: https://akizukidenshi.com/goodsaffix/bme680.pdf


## Requirements

* Python 3 or MicroPython
* I2C

Raspberry Pi の I2C は以下のコマンドで有効化できます:

```sh
sudo raspi-config
# Interface Options -> I2C で I2C を有効化する
```


## Installation (Python 3)

```sh
pip install git+https://github.com/ttk1/bme680-py.git
```


## Example Usage

```py
import time
from bme680 import BME680

if __name__ == "__main__":
    device = BME680()
    while True:
        device.measure()
        print(
            "temp: {:0.2f} °C\npress: {:0.2f} hPa\nhum: {:0.2f} %".format(
                device.temp, device.press / 100, device.hum
            )
        )
        time.sleep(3)

```


## 免責事項

このツールを使ったことによって生じた結果について、いかなる責任も負いません。 ご使用は自己責任でお願いします。
