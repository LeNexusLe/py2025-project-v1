import time
from datetime import datetime
from sensors.sensor import TemperatureSensor, HumiditySensor, PressureSensor, AirQualitySensor
from mylogger.logger import Logger
from network.client import NetworkClient
from network.config import load_client_config

logger = Logger("config.json")
logger.start()

client_config = load_client_config()
net_client = NetworkClient(
    host=client_config["host"],
    port=client_config["port"],
    timeout=client_config["timeout"],
    retries=client_config["retries"],
    logger=logger
)

sensors = [
    TemperatureSensor("temp01"),
    HumiditySensor("hum01"),
    PressureSensor("press01"),
    AirQualitySensor("air01")
]

for sensor in sensors:
    sensor.register_callback(logger.log_reading)

try:
    net_client.connect()

    for _ in range(5):
        for sensor in sensors:
            value = sensor.read_value()
            print(f"{sensor.name} ({sensor.sensor_id}): {value:.2f} {sensor.unit}")

            data = {
                "sensor_id": sensor.sensor_id,
                "timestamp": datetime.now().isoformat(),
                "value": round(value, 2),
                "unit": sensor.unit
            }

            net_client.send(data)

        print("-" * 30)
        time.sleep(1)

finally:
    net_client.close()
    logger.stop()
