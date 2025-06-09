import os
import csv
import json
from datetime import datetime, timedelta
from typing import Optional, Iterator, Dict

class Logger:
    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.root_log_dir = config["log_dir"]
        self.log_dir = os.path.join(self.root_log_dir, "archive")
        self.filename_pattern = config["filename_pattern"]
        self.buffer_size = config["buffer_size"]
        self.rotate_every_hours = config["rotate_every_hours"]
        self.max_size_mb = config["max_size_mb"]
        self.rotate_after_lines = config.get("rotate_after_lines", None)
        self.retention_days = config["retention_days"]

        os.makedirs(self.log_dir, exist_ok=True)

        self.buffer = []
        self.current_file = None
        self.current_writer = None
        self.current_filename = None
        self.last_rotation_time = datetime.now()
        self.line_count = 0

    def start(self) -> None:
        self.current_filename = datetime.now().strftime(self.filename_pattern)
        file_path = os.path.join(self.log_dir, self.current_filename)
        is_new_file = not os.path.exists(file_path)

        self.current_file = open(file_path, mode='a', newline='', encoding='utf-8')
        self.current_writer = csv.writer(self.current_file)

        if is_new_file:
            self.current_writer.writerow(["timestamp", "sensor_id", "value", "unit"])

        self.last_rotation_time = datetime.now()

    def stop(self) -> None:
        if self.current_file:
            self._flush()
            self._maybe_rotate(force=True)
            self.current_file.close()
            self.current_file = None

    def log_reading(self, sensor_id: str, timestamp: datetime, value: float, unit: str) -> None:
        self.buffer.append([timestamp.isoformat(), sensor_id, value, unit])
        if len(self.buffer) >= self.buffer_size:
            self._flush()
            self._maybe_rotate()

    def _flush(self):
        if not self.current_writer or not self.current_file:
            return
        if not self.buffer:
            return

        for row in self.buffer:
            self.current_writer.writerow(row)
        self.current_file.flush()
        self.line_count += len(self.buffer)
        self.buffer.clear()

    def _maybe_rotate(self, force=False):
        if not self.current_file:
            return

        now = datetime.now()
        file_path = os.path.join(self.log_dir, self.current_filename)

        should_rotate = force
        if not should_rotate and (now - self.last_rotation_time) >= timedelta(hours=self.rotate_every_hours):
            should_rotate = True
        if not should_rotate and os.path.getsize(file_path) >= self.max_size_mb * 1024 * 1024:
            should_rotate = True
        if not should_rotate and self.rotate_after_lines and self.line_count >= self.rotate_after_lines:
            should_rotate = True

        if should_rotate:
            self._flush()
            self.current_file.close()
            self.current_file = None
            self._clean_old_archives()

            self.current_filename = datetime.now().strftime(self.filename_pattern)
            new_path = os.path.join(self.log_dir, self.current_filename)

            if os.path.exists(new_path) and os.path.getsize(new_path) < 100:
                try:
                    os.remove(new_path)
                except Exception as e:
                    print(f"Nie udało się usunąć pustego pliku: {new_path}, błąd: {e}")

            self.start()
            self.line_count = 0
            self.last_rotation_time = now

    def _clean_old_archives(self):
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        for filename in os.listdir(self.log_dir):
            file_path = os.path.join(self.log_dir, filename)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                if mtime < cutoff:
                    os.remove(file_path)
            except Exception:
                pass

    def read_logs(self, start: datetime, end: datetime, sensor_id: Optional[str] = None) -> Iterator[Dict]:
        for filename in os.listdir(self.log_dir):
            if not filename.endswith('.csv'):
                continue
            yield from self._read_csv(os.path.join(self.log_dir, filename), start, end, sensor_id)

    def _read_csv(self, path: str, start: datetime, end: datetime, sensor_id: Optional[str]) -> Iterator[Dict]:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.fromisoformat(row["timestamp"])
                    if start <= ts <= end:
                        if sensor_id is None or row["sensor_id"] == sensor_id:
                            yield {
                                "timestamp": ts,
                                "sensor_id": row["sensor_id"],
                                "value": float(row["value"]),
                                "unit": row["unit"]
                            }
                except Exception:
                    continue

    def log_event(self, level: str, message: str) -> None:
        print(f"[{level}] {message}")
