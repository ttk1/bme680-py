# bme680-py

BME680 のデータを Python で読むための何か

* 対象のセンサーモジュール: https://akizukidenshi.com/catalog/g/gK-14469/
* BME680 のデータシート: https://akizukidenshi.com/download/ds/bosch/bme680.pdf


## Requirements

* Python 3
* I2C is enabled

I2C は以下のコマンドで有効化できます:

```sh
sudo raspi-config
# Interface Options -> I2C で I2C を有効化する
```


## Installation

```sh
pip install git+https://github.com/ttk1/bme680-py.git
```


## Example

https://github.com/ttk1/bme680-py/blob/main/example.py


## 免責事項

このツールを使ったことによって生じた結果について、いかなる責任も負いません。 ご使用は自己責任でお願いします。
