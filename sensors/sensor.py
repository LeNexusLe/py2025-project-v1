import random
import math
from datetime import datetime
import numpy as np


class Sensor:
    def __init__(self, sensor_id, name, unit, min_value, max_value, frequency=1):
        self.sensor_id = sensor_id
        self.name = name
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.frequency = frequency
        self.active = True
        self.last_value = None
        self._callbacks = []

    def register_callback(self, callback):
        self._callbacks.append(callback)

    def notify_callbacks(self, value):
        from datetime import datetime
        for cb in self._callbacks:
            cb(sensor_id=self.sensor_id, timestamp=datetime.now(), value=value, unit=self.unit)

    def read_value(self):
        if not self.active:
            raise Exception(f"Czujnik {self.name} jest wyłączony.")
        value = random.uniform(self.min_value, self.max_value)
        self.last_value = value
        self.notify_callbacks(value)
        return value

    def calibrate(self, calibration_factor):
        if self.last_value is None:
            self.read_value()
        self.last_value *= calibration_factor
        return self.last_value

    def get_last_value(self):
        if self.last_value is None:
            return self.read_value()
        return self.last_value

    def start(self):
        self.active = True

    def stop(self):
        self.active = False

    def __str__(self):
        return f"Sensor(id={self.sensor_id}, name={self.name}, unit={self.unit})"


class TemperatureSensor(Sensor):
    def __init__(self, sensor_id, frequency=1):
        super().__init__(sensor_id, "Temperature Sensor", "°C", -20, 50, frequency)

    def read_value(self):
        hour = datetime.now().hour
        base_temp = 15 + 10 * math.sin(math.pi * (hour - 6) / 12)
        noise = random.uniform(-2, 2)
        value = base_temp + noise
        value = max(self.min_value, min(self.max_value, value))
        self.last_value = value
        self.notify_callbacks(value)
        return value

class HumiditySensor(Sensor):
    def __init__(self, sensor_id, frequency=1):
        super().__init__(sensor_id, "Humidity Sensor", "%", 0, 100, frequency)

    def read_value(self):
        drift = np.random.normal(0, 5)
        value = 60 + drift
        value = max(self.min_value, min(self.max_value, value))
        self.last_value = value
        self.notify_callbacks(value)
        return value

class PressureSensor(Sensor):
    def __init__(self, sensor_id, frequency=1):
        super().__init__(sensor_id, "Pressure Sensor", "hPa", 950, 1050, frequency)

    def read_value(self):
        value = np.random.normal(1013, 5)
        value = max(self.min_value, min(self.max_value, value))
        self.last_value = value
        self.notify_callbacks(value)
        return value

class AirQualitySensor(Sensor):
    def __init__(self, sensor_id, frequency=1):
        super().__init__(sensor_id, "Air Quality Sensor", "AQI", 0, 500, frequency)

    def read_value(self):
        base_value = np.random.normal(70, 20)
        if random.random() < 0.1:
            spike = random.uniform(50, 200)
            base_value += spike
        value = max(self.min_value, min(self.max_value, base_value))
        self.last_value = value
        self.notify_callbacks(value)
        return value