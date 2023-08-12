import time
import datetime
from bme680 import BME680

device = BME680()

JST = datetime.timezone(datetime.timedelta(hours=9), "Asia/Tokyo")

while True:
    device.measure()
    print("=== {} ===".format(datetime.datetime.now(JST)))
    print(
        "temp: {:0.2f} ℃\npress: {:0.2f} hPa\nhum: {:0.2f} %".format(
            device.temp, device.press / 100, device.hum
        )
    )
    time.sleep(3)
