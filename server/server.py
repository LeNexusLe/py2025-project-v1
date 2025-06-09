import socket
import threading
import json
import sys
from network.config import load_server_config

class NetworkServer:
    def __init__(self, port: int):
        self.port = port

    def start(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', self.port))
            s.listen()
            print(f"Port: {self.port}")
            while True:
                client_socket, addr = s.accept()
                threading.Thread(target=self._handle_client, args=(client_socket, addr)).start()

    def _handle_client(self, client_socket, addr) -> None:
        with client_socket:
            try:
                raw = b""
                while True:
                    chunk = client_socket.recv(1024)
                    if not chunk:
                        break
                    raw += chunk
                    if b'\n' in chunk:
                        break

                data = json.loads(raw.decode().strip())
                print(f"\nReceived from {addr}:")
                for k, v in data.items():
                    print(f"  {k}: {v}")
                client_socket.sendall(b"ACK\n")
            except Exception as e:
                print(f"[ERROR] {e}", file=sys.stderr)


if __name__ == "__main__":
    config = load_server_config("config.yaml")
    server = NetworkServer(config["port"])
    print(f"Starting server on port {config['port']}...")
    server.start()
