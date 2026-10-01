import os
import glob
import time
import threading
from typing import Optional, Callable, List
from PySide6.QtCore import QObject, Signal
from lcd_core.usb_permissions import fix_usb_permissions, is_port_accessible

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

class SerialController(QObject):
    """
    Handles USB CDC / Serial communication with Skyloong ESP32 LCD Module.
    Thread-safe implementation emitting Qt Signals.
    """
    sig_log = Signal(str)
    sig_status_change = Signal(bool)
    sig_data_received = Signal(str)

    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 115200, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.connected = False
        self.read_thread: Optional[threading.Thread] = None
        self.running = False
        self.last_error: str = ""

    def log(self, msg: str):
        self.sig_log.emit(msg)

    @staticmethod
    def list_ports() -> List[str]:
        ports = []
        if SERIAL_AVAILABLE:
            for p in serial.tools.list_ports.comports():
                ports.append(p.device)
        # Add any found /dev/ttyACM* or /dev/ttyUSB*
        for dev in glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"):
            if dev not in ports:
                ports.append(dev)
        return sorted(ports)

    def connect(self, port: Optional[str] = None, baudrate: Optional[int] = None, auto_fix_perm: bool = True) -> bool:
        self.last_error = ""
        if not SERIAL_AVAILABLE:
            self.last_error = "Moduł 'pyserial' nie jest zainstalowany."
            self.log(f"Błąd: {self.last_error}")
            return False

        if port:
            self.port = port
        if baudrate:
            self.baudrate = baudrate

        if self.connected:
            self.disconnect()

        # Check permissions and attempt auto-fix if necessary
        if os.path.exists(self.port) and not is_port_accessible(self.port):
            if auto_fix_perm:
                self.log(f"Wykryto brak uprawnień do {self.port}. Uruchamiam autoryzację systemową...")
                ok, msg = fix_usb_permissions(self.port)
                self.log(msg)
                if not ok:
                    self.last_error = msg
                    return False
            else:
                self.last_error = f"Brak uprawnień do portu {self.port}."
                return False

        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                write_timeout=1.0
            )
            self.connected = True
            self.running = True
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()

            self.log(f"Połączono z portem {self.port} ({self.baudrate} baud)")
            self.sig_status_change.emit(True)
            return True
        except PermissionError as pe:
            if auto_fix_perm:
                self.log(f"Odmowa dostępu do {self.port}. Próba automatycznej naprawy uprawnień...")
                ok, msg = fix_usb_permissions(self.port)
                if ok:
                    # Retry once
                    return self.connect(port=self.port, baudrate=self.baudrate, auto_fix_perm=False)
                else:
                    self.last_error = msg
            else:
                self.last_error = f"Brak uprawnień do portu {self.port}."
            self.log(f"Błąd: {self.last_error}")
            self.connected = False
            self.sig_status_change.emit(False)
            return False
        except Exception as e:
            err_str = str(e)
            if ("Permission denied" in err_str or "[Errno 13]" in err_str) and auto_fix_perm:
                self.log(f"Odmowa dostępu do {self.port}. Próba automatycznej naprawy uprawnień...")
                ok, msg = fix_usb_permissions(self.port)
                if ok:
                    return self.connect(port=self.port, baudrate=self.baudrate, auto_fix_perm=False)
                else:
                    self.last_error = msg
            else:
                self.last_error = f"Błąd otwierania portu {self.port}: {err_str}"
            self.log(self.last_error)
            self.connected = False
            self.sig_status_change.emit(False)
            return False

    def disconnect(self):
        self.running = False
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception:
                pass
            self.serial_conn = None
        self.connected = False
        self.log(f"Rozłączono port {self.port}")
        self.sig_status_change.emit(False)

    def send_data(self, data: bytes) -> bool:
        if not self.connected or not self.serial_conn:
            return False
        try:
            self.serial_conn.write(data)
            self.serial_conn.flush()
            return True
        except Exception as e:
            self.log(f"Błąd wysyłania danych: {e}")
            return False

    def send_command(self, cmd_bytes: bytes, port: Optional[str] = None) -> Tuple[bool, str]:
        """
        Sends a command byte sequence to ESP32 over USB CDC.
        If already connected, sends immediately.
        If disconnected, briefly connects, sends, and disconnects.
        """
        if self.connected and self.serial_conn and self.serial_conn.is_open:
            if self.send_data(cmd_bytes):
                return True, "Wysłano polecenie po aktywnym połączeniu USB."
            return False, "Nie udało się wysłać danych przez otwarty port."

        target_port = port or self.port
        if not os.path.exists(target_port):
            return False, f"Port {target_port} nie istnieje (odłączony kabel USB?)."

        if not is_port_accessible(target_port):
            ok, msg = fix_usb_permissions(target_port)
            if not ok:
                return False, f"Brak uprawnień do {target_port}: {msg}"

        try:
            s = serial.Serial(port=target_port, baudrate=self.baudrate, timeout=1.0, write_timeout=1.0)
            s.write(cmd_bytes)
            s.flush()
            time.sleep(0.05)
            s.close()
            return True, f"Wysłano polecenie do {target_port}."
        except Exception as e:
            return False, f"Błąd połączenia USB ({target_port}): {str(e)}"

    def switch_app(self, port: Optional[str] = None) -> Tuple[bool, str]:
        """
        Sends backtick (` / 0x60) over USB to switch to next app on the screen
        (Clock -> APS -> GIF -> Weather -> Sysinfo PC Monitor).
        """
        self.log("Wysyłanie sygnału przełączenia aplikacji (USB `)...")
        ok, msg = self.send_command(b'`', port=port)
        if ok:
            self.log("Pomyślnie wysłano sygnał zmiany trybu ekranu (`).")
        else:
            self.log(f"Niepowodzenie: {msg}")
        return ok, msg

    def toggle_settings_menu(self, port: Optional[str] = None) -> Tuple[bool, str]:
        """Sends '/' (0x2F) over USB to enter/exit settings menu on screen."""
        self.log("Wysyłanie sygnału menu ustawień (USB /)...")
        return self.send_command(b'/', port=port)

    def nav_up(self, port: Optional[str] = None) -> Tuple[bool, str]:
        """Sends 'w' (Up / Prev)."""
        return self.send_command(b'w', port=port)

    def nav_down(self, port: Optional[str] = None) -> Tuple[bool, str]:
        """Sends 's' (Down / Next)."""
        return self.send_command(b's', port=port)

    def nav_left(self, port: Optional[str] = None) -> Tuple[bool, str]:
        """Sends 'a' (Left)."""
        return self.send_command(b'a', port=port)

    def nav_right(self, port: Optional[str] = None) -> Tuple[bool, str]:
        """Sends 'd' (Right)."""
        return self.send_command(b'd', port=port)

    def nav_enter(self, port: Optional[str] = None) -> Tuple[bool, str]:
        """Sends '\\n' (Enter)."""
        return self.send_command(b'\n', port=port)

    def _read_loop(self):
        while self.running and self.serial_conn and self.serial_conn.is_open:
            try:
                line = self.serial_conn.readline()
                if line:
                    decoded = line.decode('utf-8', errors='ignore').strip()
                    if decoded:
                        self.sig_data_received.emit(decoded)
            except Exception:
                if self.running:
                    time.sleep(0.1)
                break
        self.connected = False
        self.sig_status_change.emit(False)
