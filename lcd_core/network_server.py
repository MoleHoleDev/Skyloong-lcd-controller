import socket
import struct
import time
import threading
import psutil
from typing import Optional, Callable, List, Tuple

class NetworkServer:
    """
    TCP Telemetry Server for Skyloong GK104 Pro LCD Screen.
    Transmits real-time CPU/RAM (and extended) telemetry to connected keyboard screens.
    Default port: 1648.
    """

    @staticmethod
    def get_process_using_port(port: int) -> Optional[Tuple[int, str]]:
        """Finds PID and name of any process listening on the given port."""
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr and conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            return conn.pid, proc.name()
                        except Exception:
                            return conn.pid, "Nieznany proces"
        except Exception:
            pass
        return None

    @staticmethod
    def kill_process_on_port(port: int) -> bool:
        """Kills any process currently occupying the given port."""
        info = NetworkServer.get_process_using_port(port)
        if not info:
            return True
        pid, name = info
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            try:
                proc.wait(timeout=2)
                return True
            except psutil.TimeoutExpired:
                proc.kill()
                return True
        except Exception:
            return False

    def __init__(self, host: str = "0.0.0.0", port: int = 1648):
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.clients: List[Tuple[socket.socket, Tuple[str, int]]] = []
        self.running = False
        self.server_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_log: Optional[Callable[[str], None]] = None
        self.on_status_change: Optional[Callable[[bool], None]] = None
        self.on_clients_change: Optional[Callable[[int], None]] = None
        
        # Telemetry data provider
        self.metrics_getter: Optional[Callable[[], dict]] = None

    def log(self, msg: str):
        if self.on_log:
            self.on_log(msg)
        else:
            print(f"[TCP Server] {msg}")

    def start(self, host: Optional[str] = None, port: Optional[int] = None) -> bool:
        if self.running:
            return True

        if host:
            self.host = host
        if port:
            self.port = port

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True

            self.server_thread = threading.Thread(target=self._run_server, daemon=True)
            self.server_thread.start()

            self.log(f"Serwer nasłuchuje na {self.host}:{self.port}")
            if self.on_status_change:
                self.on_status_change(True)
            return True
        except Exception as e:
            self.log(f"Błąd uruchamiania serwera TCP: {e}")
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception:
                    pass
            self.running = False
            if self.on_status_change:
                self.on_status_change(False)
            return False

    def stop(self):
        if not self.running:
            return

        self.running = False
        for client_sock, _ in self.clients:
            try:
                client_sock.close()
            except Exception:
                pass
        self.clients.clear()

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None

        self.log("Serwer TCP został zatrzymany")
        if self.on_status_change:
            self.on_status_change(False)
        if self.on_clients_change:
            self.on_clients_change(0)

    def _run_server(self):
        accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        accept_thread.start()

    def _accept_loop(self):
        while self.running and self.server_socket:
            try:
                self.server_socket.settimeout(1.0)
                client_sock, client_addr = self.server_socket.accept()
                self.clients.append((client_sock, client_addr))
                self.log(f"Nowe połączenie od: {client_addr[0]}:{client_addr[1]}")
                if self.on_clients_change:
                    self.on_clients_change(len(self.clients))

                cthread = threading.Thread(target=self._handle_client, args=(client_sock, client_addr), daemon=True)
                cthread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    self.log(f"Błąd akceptacji połączenia: {e}")
                break

    def _handle_client(self, client_sock: socket.socket, client_addr: Tuple[str, int]):
        client_sock.settimeout(2.0)
        while self.running:
            try:
                cpu_val = 0.0
                mem_val = 0.0
                if self.metrics_getter:
                    m = self.metrics_getter()
                    cpu_val = float(m.get('cpu_percent', 0.0))
                    mem_val = float(m.get('ram_percent', 0.0))

                # ESP32 Sysinfo firmware expects values in 0.0-1.0 range (it multiplies by 100)
                if cpu_val > 1.0:
                    cpu_val = cpu_val / 100.0
                if mem_val > 1.0:
                    mem_val = mem_val / 100.0

                # Standard 8-byte payload expected by GK104 Pro screen firmware
                payload = struct.pack('<ff', float(cpu_val), float(mem_val))
                client_sock.sendall(payload)

                # Wait for 1-byte ACK from client screen
                try:
                    ack = client_sock.recv(1)
                    if not ack:
                        break
                except socket.timeout:
                    pass

                time.sleep(0.3)
            except Exception:
                break

        # Cleanup disconnected client
        try:
            client_sock.close()
        except Exception:
            pass
        self.clients = [c for c in self.clients if c[0] != client_sock]
        self.log(f"Rozłączono klienta: {client_addr[0]}")
        if self.on_clients_change:
            self.on_clients_change(len(self.clients))
