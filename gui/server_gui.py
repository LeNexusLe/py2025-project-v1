import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from network.config import load_server_config
from server.server import NetworkServer


class SensorRecord:
    def __init__(self):
        self.history = deque()

    def add(self, timestamp: datetime, value: float):
        self.history.append((timestamp, value))
        cutoff = timestamp - timedelta(hours=12)
        while self.history and self.history[0][0] < cutoff:
            self.history.popleft()

    def avg(self, period_hours: float, now: datetime):
        cutoff = now - timedelta(hours=period_hours)
        values = [v for t, v in self.history if t >= cutoff]
        return sum(values) / len(values) if values else 0.0

class ServerGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Network Server GUI")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self._build_top()
        self._build_table()
        self._build_statusbar()

        self.records = defaultdict(SensorRecord)
        self.server = None
        self.server_thread = None
        self.listening = False

    def _build_top(self):
        frame = ttk.Frame(self)
        frame.pack(fill='x', padx=8, pady=4)

        ttk.Label(frame, text="Port:").pack(side='left')
        self.port_var = tk.StringVar(value=str(load_server_config().get('port', 9000)))
        ttk.Entry(frame, textvariable=self.port_var, width=6).pack(side='left', padx=4)

        ttk.Button(frame, text="Start", command=self.start_server).pack(side='left', padx=4)
        ttk.Button(frame, text="Stop", command=self.stop_server).pack(side='left', padx=4)

    def _build_table(self):
        cols = ("sensor","value","unit","ts","avg1h","avg12h")
        self.tree = ttk.Treeview(self, columns=cols, show='headings', height=10)
        headings = ["Sensor","Wartość","Jednostka","Timestamp","Śr. 1h","Śr.12h"]
        for col, hd in zip(cols, headings):
            self.tree.heading(col, text=hd)
            self.tree.column(col, width=100, anchor='center')
        self.tree.pack(fill='both', expand=True, padx=8, pady=4)

    def _build_statusbar(self):
        self.status_var = tk.StringVar(value="Zatrzymany")
        lbl = ttk.Label(self, textvariable=self.status_var, anchor='w')
        lbl.pack(fill='x', padx=4, pady=2)

    def start_server(self):
        if self.listening:
            return
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Błąd", "Niepoprawny numer portu")
            return

        self.server = NetworkServer(port, callback=self.handle_data, err_callback=self.show_error)
        self.server_thread = threading.Thread(target=self.server.start, daemon=True)
        self.server_thread.start()
        self.listening = True
        self.status_var.set(f"Nasłuchuje na porcie {port}")
        self.after(1000, self.refresh_table)

    def stop_server(self):
        if self.server and self.listening:
            self.server.stop()
        self.listening = False
        self.status_var.set("Zatrzymany")

    def on_close(self):
        self.stop_server()
        self.destroy()

    def handle_data(self, data: dict):
        ts = datetime.fromisoformat(data["timestamp"])
        sensor = data["sensor_id"]
        unit = data["unit"]
        value = float(data["value"])

        rec = self.records[sensor]
        rec.add(ts, value)
        setattr(rec, "unit", unit)

    def refresh_table(self):
        now = datetime.now()
        self.tree.delete(*self.tree.get_children())
        for sensor, rec in self.records.items():
            row = (
                sensor,
                f"{rec.history and rec.history[-1][1]:.2f}",
                getattr(rec, "unit", ""),
                rec.history and rec.history[-1][0].strftime("%Y-%m-%d %H:%M:%S"),
                f"{rec.avg(1, now):.2f}",
                f"{rec.avg(12, now):.2f}"
            )
            self.tree.insert("", "end", values=row)
        if self.listening:
            self.after(1000, self.refresh_table)

    def show_error(self, msg: str):
        messagebox.showerror("Serwer ERROR", msg)
        self.stop_server()
