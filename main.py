from sensors.sensor import TemperatureSensor, HumiditySensor, PressureSensor, AirQualitySensor
from mylogger.logger import Logger
import time

logger = Logger("config.json")
logger.start()

sensors = [
    TemperatureSensor("temp01"),
    HumiditySensor("hum01"),
    PressureSensor("press01"),
    AirQualitySensor("air01")
]

for sensor in sensors:
    sensor.register_callback(logger.log_reading)

try:
    for _ in range(5):
        for sensor in sensors:
            value = sensor.read_value()
            print(f"{sensor.name} ({sensor.sensor_id}): {value:.2f} {sensor.unit}")
        print("-" * 30)
        time.sleep(1)
finally:
    logger.stop()
