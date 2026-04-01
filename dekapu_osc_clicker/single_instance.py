import socket
import threading
from contextlib import closing

HOST = "127.0.0.1"
PORT = 47653
WAKE_MESSAGE = b"SHOW_WINDOW"


class SingleInstanceManager:
    def __init__(self, on_wake=None):
        self.on_wake = on_wake or (lambda: None)
        self._server = None
        self._thread = None
        self._running = False
        self.is_primary_instance = False

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((HOST, PORT))
            server.listen(5)
        except OSError:
            server.close()
            self.is_primary_instance = False
            return False

        self._server = server
        self._running = True
        self.is_primary_instance = True
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        return True

    def _serve(self):
        while self._running and self._server is not None:
            try:
                conn, _addr = self._server.accept()
            except OSError:
                break
            with closing(conn):
                try:
                    data = conn.recv(1024)
                except OSError:
                    continue
                if data == WAKE_MESSAGE:
                    try:
                        self.on_wake()
                    except Exception:
                        pass

    @staticmethod
    def notify_existing_instance():
        try:
            with socket.create_connection((HOST, PORT), timeout=1) as conn:
                conn.sendall(WAKE_MESSAGE)
            return True
        except OSError:
            return False

    def stop(self):
        self._running = False
        if self._server is not None:
            try:
                self._server.close()
            except OSError:
                pass
            self._server = None
