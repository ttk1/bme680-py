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
