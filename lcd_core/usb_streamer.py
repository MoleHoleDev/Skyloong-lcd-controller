"""
USB Frame Streamer for Skyloong GK104 Pro LCD Screen.
Communicates directly with ESP32-S3 over USB CDC serial protocol.
Streams compressed JPEG or Raw RGB565 frames at high FPS (up to 60 FPS).
"""

import os
import sys
import time
import struct
import io
import threading
from typing import Optional, Tuple, Dict, Any
from PIL import Image

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

from PySide6.QtCore import QObject, Signal, QThread
from .usb_permissions import fix_usb_permissions, is_port_accessible


class USBProtocol:
    MAGIC = b'SKYL'
    CMD_DRAW_JPEG = 0x01
    CMD_DRAW_RAW565 = 0x02
    CMD_SET_BRIGHTNESS = 0x03
    CMD_PING = 0x04
    CMD_SCREEN_POWER = 0x05
    CMD_CLEAR_SCREEN = 0x06
    CMD_RESET_BOOTLOADER = 0x09

    ACK = 0x06
    NAK = 0x15


class USBStreamController(QObject):
    """
    Handles direct USB communication with the custom Skyloong USB Screen Firmware.
    """
    status_changed = Signal(bool, str)
    stats_updated = Signal(dict)
    log_message = Signal(str)

    def __init__(self, port: str = "/dev/ttyACM0", baudrate: int = 115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial_conn: Optional[serial.Serial] = None
        self.connected = False
        self._lock = threading.Lock()

        # Stats
        self.frames_sent = 0
        self.bytes_sent = 0
        self.total_frames_sent = 0
        self.last_stat_time = time.time()
        self.fps = 0.0
        self.kbps = 0.0
        self.last_latency_ms = 0.0

    def log(self, msg: str):
        self.log_message.emit(msg)

    @property
    def is_open(self) -> bool:
        with self._lock:
            return bool(self.connected and self.serial_conn and self.serial_conn.is_open)

    @property
    def ser(self):
        return self.serial_conn

    def connect_usb(self, port: Optional[str] = None) -> Tuple[bool, str]:
        with self._lock:
            if port:
                self.port = port

            if self.connected and self.serial_conn and self.serial_conn.is_open:
                return True, "Połączono"

            if not os.path.exists(self.port):
                return False, f"Port {self.port} nie istnieje. Podłącz ekran kablem USB."

            if not is_port_accessible(self.port):
                ok, msg = fix_usb_permissions(self.port)
                if not ok:
                    return False, f"Brak uprawnień do {self.port}: {msg}"

            try:
                self.serial_conn = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=0.5,
                    write_timeout=0.5
                )
                self.connected = True
                self.frames_sent = 0
                self.bytes_sent = 0
                self.last_stat_time = time.time()
                self.status_changed.emit(True, f"Połączono z {self.port}")
                self.log(f"🟢 Otwarto port USB dla streamowania klatek: {self.port}")
                return True, "Połączono"
            except Exception as e:
                self.connected = False
                self.status_changed.emit(False, str(e))
                self.log(f"❌ Błąd połączenia USB ({self.port}): {e}")
                return False, str(e)

    def disconnect_usb(self):
        with self._lock:
            if self.serial_conn:
                try:
                    self.serial_conn.close()
                except Exception:
                    pass
            self.serial_conn = None
            self.connected = False
            self.status_changed.emit(False, "Rozłączono")
            self.log("⚪ Zamknięto połączenie USB streamera.")

    def send_jpeg_frame(self, pil_image: Image.Image, quality: int = 80) -> bool:
        """
        Compresses image to JPEG and sends via USB CDC protocol.
        """
        if not self.connected or not self.serial_conn:
            return False

        # Resize if not 320x240
        if pil_image.size != (320, 240):
            pil_image = pil_image.resize((320, 240), Image.Resampling.LANCZOS)

        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")

        # Encode JPEG in-memory
        buf = io.BytesIO()
        pil_image.save(buf, format="JPEG", quality=quality, optimize=False)
        jpeg_data = buf.getvalue()
        jpeg_len = len(jpeg_data)

        # Build Packet: MAGIC (4) + CMD (1) + LEN (4) + JPEG_BYTES
        header = struct.pack('<4sBI', USBProtocol.MAGIC, USBProtocol.CMD_DRAW_JPEG, jpeg_len)
        packet = header + jpeg_data

        t0 = time.perf_counter()
        with self._lock:
            try:
                self.serial_conn.write(packet)
                self.serial_conn.flush()

                # Read 1-byte ACK
                ack = self.serial_conn.read(1)
                t1 = time.perf_counter()
                self.last_latency_ms = (t1 - t0) * 1000.0

                if ack and ack[0] == USBProtocol.ACK:
                    self.frames_sent += 1
                    self.total_frames_sent += 1
                    self.bytes_sent += len(packet)
                    self._update_stats()
                    return True
                else:
                    return False
            except Exception as e:
                self.log(f"⚠️ Błąd wysyłania klatki JPEG: {e}")
                self.disconnect_usb()
                return False

    def send_raw565_frame(self, rgb565_bytes: bytes, x: int = 0, y: int = 0, w: int = 320, h: int = 240) -> bool:
        """
        Sends raw RGB565 byte buffer to ST7789 display.
        """
        if not self.connected or not self.serial_conn:
            return False

        header = struct.pack('<4sBHHHHI', USBProtocol.MAGIC, USBProtocol.CMD_DRAW_RAW565, x, y, w, h, len(rgb565_bytes))
        packet = header + rgb565_bytes

        with self._lock:
            try:
                self.serial_conn.write(packet)
                self.serial_conn.flush()
                ack = self.serial_conn.read(1)
                if ack and ack[0] == USBProtocol.ACK:
                    self.frames_sent += 1
                    self.bytes_sent += len(packet)
                    self._update_stats()
                    return True
                return False
            except Exception as e:
                self.log(f"⚠️ Błąd wysyłania klatki RAW565: {e}")
                self.disconnect_usb()
                return False

    def set_brightness(self, brightness: int) -> bool:
        """Sets display brightness (0 - 255)."""
        if not self.connected or not self.serial_conn:
            return False
        brightness = max(0, min(255, int(brightness)))
        packet = struct.pack('<4sBB', USBProtocol.MAGIC, USBProtocol.CMD_SET_BRIGHTNESS, brightness)
        with self._lock:
            try:
                self.serial_conn.write(packet)
                self.serial_conn.flush()
                ack = self.serial_conn.read(1)
                return bool(ack and ack[0] == USBProtocol.ACK)
            except Exception:
                return False

    def set_power(self, power_on: bool) -> bool:
        """Turns display panel on or off."""
        if not self.connected or not self.serial_conn:
            return False
        val = 1 if power_on else 0
        packet = struct.pack('<4sBB', USBProtocol.MAGIC, USBProtocol.CMD_SCREEN_POWER, val)
        with self._lock:
            try:
                self.serial_conn.write(packet)
                self.serial_conn.flush()
                ack = self.serial_conn.read(1)
                return bool(ack and ack[0] == USBProtocol.ACK)
            except Exception:
                return False

    def ping_device(self) -> Optional[Dict[str, Any]]:
        """Pings device to get hardware telemetry and stats."""
        if not self.connected or not self.serial_conn:
            return None
        packet = struct.pack('<4sB', USBProtocol.MAGIC, USBProtocol.CMD_PING)
        with self._lock:
            try:
                self.serial_conn.write(packet)
                self.serial_conn.flush()
                resp = self.serial_conn.read(13)
                if len(resp) == 13 and resp[:4] == b'SKPG':
                    fps, bright, uptime = struct.unpack('<fBI', resp[4:])
                    return {
                        "device_fps": fps,
                        "brightness": bright,
                        "uptime_ms": uptime
                    }
                return None
            except Exception:
                return None

    def _update_stats(self):
        now = time.time()
        dt = now - self.last_stat_time
        if dt >= 1.0:
            self.fps = self.frames_sent / dt
            self.kbps = (self.bytes_sent / 1024.0) / dt
            self.frames_sent = 0
            self.bytes_sent = 0
            self.last_stat_time = now
            self.stats_updated.emit({
                "fps": self.fps,
                "kbps": self.kbps,
                "latency_ms": self.last_latency_ms
            })


class USBStreamThread(QThread):
    """
    Dedicated worker thread to stream frames continuously from ScreenRenderer to USB screen.
    """
    fps_report = Signal(float, float, float)  # fps, kbps, latency_ms
    stats_updated = Signal(float, float)      # fps, kbps
    error_occurred = Signal(str)
    status_changed = Signal(bool, str)

    def __init__(self, controller: USBStreamController, renderer_callback=None, fps: int = 30, quality: int = 85, port: Optional[str] = None):
        super().__init__()
        self.controller = controller
        self.renderer_callback = renderer_callback
        self.target_fps = max(1, min(60, int(fps)))
        self.quality = max(20, min(95, int(quality)))
        self.port = port
        self.running = False
        self._stats_connected = False

    def set_target_fps(self, fps: int):
        self.target_fps = max(1, min(60, int(fps)))

    def set_quality(self, quality: int):
        self.quality = max(20, min(95, int(quality)))

    def run(self):
        self.running = True
        
        # Connect controller signals safely
        try:
            self.controller.stats_updated.connect(self._on_controller_stats)
        except Exception:
            pass

        # Ensure USB connection is active
        if not self.controller.is_open:
            port_to_use = self.port or self.controller.port
            ok, msg = self.controller.connect_usb(port_to_use)
            if not ok:
                self.error_occurred.emit(msg)
                self.running = False
                return

        while self.running:
            frame_start = time.perf_counter()

            if self.controller.is_open:
                try:
                    img = None
                    if callable(self.renderer_callback):
                        img = self.renderer_callback()
                    elif hasattr(self.renderer_callback, 'get_current_frame'):
                        img = self.renderer_callback.get_current_frame()

                    if img is not None:
                        ok = self.controller.send_jpeg_frame(img, quality=self.quality)
                        if not ok and self.running:
                            # Re-verify port if failed
                            time.sleep(0.05)
                except Exception as e:
                    self.error_occurred.emit(str(e))
                    time.sleep(0.1)
            else:
                # Connection dropped, attempt reconnect
                time.sleep(0.2)
                if self.running:
                    self.controller.connect_usb(self.port)

            elapsed = time.perf_counter() - frame_start
            target_period = 1.0 / float(max(1, self.target_fps))
            sleep_time = target_period - elapsed
            if sleep_time > 0.001:
                time.sleep(sleep_time)

    def _on_controller_stats(self, stats: dict):
        fps = stats.get("fps", 0.0)
        kbps = stats.get("kbps", 0.0)
        lat = stats.get("latency_ms", 0.0)
        self.fps_report.emit(fps, kbps, lat)
        self.stats_updated.emit(fps, kbps)

    def stop(self):
        self.running = False
        self.wait(1000)
