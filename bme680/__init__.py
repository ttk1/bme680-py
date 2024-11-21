import sys

if sys.implementation.name == "micropython":
    from bme680.bme680_micropython import BME680
else:
    from bme680.bme680_python import BME680
