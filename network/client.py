import socket
import json
from typing import Optional
from mylogger.logger import Logger
from network.config import load_client_config

class NetworkClient:
    def __init__(self, host: str, port: int, timeout: float = 5.0, retries: int = 3, logger: Optional[Logger] = None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.logger = logger
        self.socket = None

    def connect(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        print(f"[CLIENT] Connecting to {self.host}:{self.port}...")
        self.socket.connect((self.host, self.port))
        print("[CLIENT] Connected")
        if self.logger:
            self.logger.log_event("INFO", f"Connected to {self.host}:{self.port}")

    def send(self, data: dict) -> bool:
        payload = self._serialize(data)
        for attempt in range(1, self.retries + 1):
            try:
                print(f"[CLIENT] Sending data, attempt {attempt}: {data}")
                self.socket.sendall(payload + b'\n')
                ack = self.socket.recv(1024)
                if ack.strip() == b"ACK":
                    print("[CLIENT] ACK received")
                    if self.logger:
                        self.logger.log_event("INFO", "ACK received")
                    return True
                else:
                    print(f"[CLIENT] Unexpected response: {ack}")
            except Exception as e:
                print(f"[CLIENT ERROR] Send attempt {attempt} failed: {e}")
                if self.logger:
                    self.logger.log_event("ERROR", f"Send attempt {attempt} failed: {e}")
        return False

    def close(self) -> None:
        if self.socket:
            print("[CLIENT] Closing connection")
            self.socket.close()
            if self.logger:
                self.logger.log_event("INFO", "Connection closed")

    def _serialize(self, data: dict) -> bytes:
        return json.dumps(data).encode("utf-8")

    def _deserialize(self, raw: bytes) -> dict:
        return json.loads(raw.decode("utf-8"))