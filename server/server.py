import socket
import threading
import json
import sys
from network.config import load_server_config


class NetworkServer:
    def __init__(self, port: int, callback=None, err_callback=None):
        self.port = port
        self.callback = callback
        self.err_callback = err_callback
        self._server_socket = None
        self._running = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            print("Server already running.")
            return

        self._running.set()
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

    def stop(self):
        self._running.clear()
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception as e:
                print(f"[ERROR] Closing socket: {e}", file=sys.stderr)

    def _run_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            self._server_socket = s
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', self.port))
            s.listen()
            print(f"[INFO] Server listening on port {self.port}")

            while self._running.is_set():
                try:
                    s.settimeout(1.0)
                    client_socket, addr = s.accept()
                    threading.Thread(target=self._handle_client, args=(client_socket, addr), daemon=True).start()
                except socket.timeout:
                    continue
                except OSError:
                    break

    def _handle_client(self, client_socket, addr):
        with client_socket:
            try:
                buffer = b""
                while self._running.is_set():
                    chunk = client_socket.recv(1024)
                    if not chunk:
                        break
                    buffer += chunk
                    while b'\n' in buffer:
                        line, buffer = buffer.split(b'\n', 1)
                        data = json.loads(line.decode().strip())
                        print(f"\nReceived from {addr}: {data}")
                        if self.callback:
                            self.callback(data)
                        client_socket.sendall(b"ACK\n")
            except Exception as e:
                if self.err_callback:
                    self.err_callback(str(e))
                else:
                    print(f"[ERROR] {e}", file=sys.stderr)
