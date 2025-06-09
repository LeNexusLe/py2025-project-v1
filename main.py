from sensors.sensor import TemperatureSensor, HumiditySensor, PressureSensor, LightSensor
import time

sensors = [
    TemperatureSensor("temp01"),
    HumiditySensor("hum01"),
    PressureSensor("press01"),
    LightSensor("light01")
]

for i in range(5):
    for sensor in sensors:
        print(f"{sensor.name}: {sensor.read_value():.2f} {sensor.unit}")
    print("-" * 30)
    time.sleep(1)