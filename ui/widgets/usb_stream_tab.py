"""
USB Live Streamer Tab for Skyloong GK104 Pro LCD Screen.
Provides full GUI controls for direct USB frame streaming, FPS/quality settings,
hardware brightness/power controls, and one-click ESP32 firmware flashing.
"""

import os
import sys
import glob
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QSpinBox, QGroupBox, QScrollArea,
    QFrame, QMessageBox, QProgressBar, QTextEdit, QDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from lcd_core.usb_streamer import USBStreamController, USBStreamThread
from lcd_core.usb_permissions import fix_usb_permissions, is_port_accessible


class USBStreamTab(QWidget):
    streaming_toggled = Signal(bool)

    def __init__(self, stream_controller: USBStreamController, get_current_frame_cb, parent=None):
        super().__init__(parent)
        self.stream_ctrl = stream_controller
        self.get_current_frame_cb = get_current_frame_cb

        self.stream_thread = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header Info Banner
        header_frame = QFrame()
        header_frame.setObjectName("Panel")
        header_frame.setStyleSheet("""
            QFrame#Panel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #1e1b4b);
                border: 1px solid #6366f1;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        h_layout = QVBoxLayout(header_frame)
        title_lbl = QLabel("🚀 Bezpośredni Streaming Klatek przez USB (No Wi-Fi)")
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #a5b4fc;")
        desc_lbl = QLabel(
            "Ten tryb przesyła wyrenderowane klatki wirtualnego ekranu (zegary, statystyki, kalendarz, zdjęcia, GIF-y)\n"
            "bezpośrednio przez kabel USB-C (/dev/ttyACM*) z prędkością do 60 FPS, z pominięciem Wi-Fi!"
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        h_layout.addWidget(title_lbl)
        h_layout.addWidget(desc_lbl)
        layout.addWidget(header_frame)

        # Section 1: USB Connection
        conn_box = QGroupBox("1. Połączenie z portem USB ekranu")
        conn_layout = QVBoxLayout(conn_box)

        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Wykryty port USB:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_row.addWidget(self.port_combo, 2)

        self.refresh_btn = QPushButton("🔄 Odśwież")
        self.refresh_btn.clicked.connect(self.refresh_ports)
        port_row.addWidget(self.refresh_btn)

        self.connect_btn = QPushButton("🔌 Połącz USB")
        self.connect_btn.setObjectName("AccentButton")
        self.connect_btn.clicked.connect(self.toggle_usb_connect)
        port_row.addWidget(self.connect_btn)
        conn_layout.addLayout(port_row)

        self.status_lbl = QLabel("Status połączenia: ⚪ Rozłączony")
        self.status_lbl.setStyleSheet("font-weight: bold; color: #94a3b8;")
        conn_layout.addWidget(self.status_lbl)
        layout.addWidget(conn_box)

        # Section 2: Stream Controls & Performance
        stream_box = QGroupBox("2. Kontrola Strumieniowania na Żywo (Live Stream)")
        stream_layout = QVBoxLayout(stream_box)

        btn_row = QHBoxLayout()
        self.start_stream_btn = QPushButton("▶ Rozpocznij Strumieniowanie USB")
        self.start_stream_btn.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #10b981;
            }
        """)
        self.start_stream_btn.clicked.connect(self.toggle_streaming)
        btn_row.addWidget(self.start_stream_btn, 2)
        stream_layout.addLayout(btn_row)

        # FPS Slider
        fps_row = QHBoxLayout()
        fps_row.addWidget(QLabel("Docelowy klatkaż (FPS):"))
        self.fps_slider = QSlider(Qt.Horizontal)
        self.fps_slider.setRange(5, 60)
        self.fps_slider.setValue(30)
        self.fps_slider.valueChanged.connect(self.on_fps_changed)
        fps_row.addWidget(self.fps_slider, 2)

        self.fps_val_lbl = QLabel("30 FPS")
        self.fps_val_lbl.setMinimumWidth(50)
        fps_row.addWidget(self.fps_val_lbl)
        stream_layout.addLayout(fps_row)

        # JPEG Quality Slider
        qual_row = QHBoxLayout()
        qual_row.addWidget(QLabel("Jakość kompresji JPEG:"))
        self.qual_slider = QSlider(Qt.Horizontal)
        self.qual_slider.setRange(30, 95)
        self.qual_slider.setValue(80)
        self.qual_slider.valueChanged.connect(self.on_qual_changed)
        qual_row.addWidget(self.qual_slider, 2)

        self.qual_val_lbl = QLabel("80%")
        self.qual_val_lbl.setMinimumWidth(50)
        qual_row.addWidget(self.qual_val_lbl)
        stream_layout.addLayout(qual_row)

        # Real-time Telemetry Metrics Frame
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet("background: #090d16; border-radius: 6px; padding: 8px; border: 1px solid #1e293b;")
        m_layout = QHBoxLayout(metrics_frame)

        self.live_fps_lbl = QLabel("Rzeczywiste FPS: 0.0")
        self.live_fps_lbl.setStyleSheet("color: #00f0ff; font-weight: bold;")
        m_layout.addWidget(self.live_fps_lbl)

        self.live_bitrate_lbl = QLabel("Pasmo: 0.0 KB/s")
        self.live_bitrate_lbl.setStyleSheet("color: #a855f7; font-weight: bold;")
        m_layout.addWidget(self.live_bitrate_lbl)

        self.live_latency_lbl = QLabel("Opóźnienie ACK: 0.0 ms")
        self.live_latency_lbl.setStyleSheet("color: #10b981; font-weight: bold;")
        m_layout.addWidget(self.live_latency_lbl)

        stream_layout.addWidget(metrics_frame)
        layout.addWidget(stream_box)

        # Section 3: Hardware Display Controls
        hw_box = QGroupBox("3. Sprzętowe sterowanie wyświetlaczem LCD")
        hw_layout = QVBoxLayout(hw_box)

        bright_row = QHBoxLayout()
        bright_row.addWidget(QLabel("Jasność podświetlenia:"))
        self.bright_slider = QSlider(Qt.Horizontal)
        self.bright_slider.setRange(0, 255)
        self.bright_slider.setValue(200)
        self.bright_slider.valueChanged.connect(self.on_brightness_changed)
        bright_row.addWidget(self.bright_slider, 2)

        self.bright_val_lbl = QLabel("78%")
        bright_row.addWidget(self.bright_val_lbl)
        hw_layout.addLayout(bright_row)

        hw_btn_row = QHBoxLayout()
        self.screen_on_btn = QPushButton("💡 Włącz ekran")
        self.screen_on_btn.clicked.connect(lambda: self.stream_ctrl.set_power(True))
        hw_btn_row.addWidget(self.screen_on_btn)

        self.screen_off_btn = QPushButton("🌙 Wygaś ekran")
        self.screen_off_btn.clicked.connect(lambda: self.stream_ctrl.set_power(False))
        hw_btn_row.addWidget(self.screen_off_btn)
        hw_layout.addLayout(hw_btn_row)
        layout.addWidget(hw_box)

        # Section 4: Firmware Flashing Tool
        flash_box = QGroupBox("4. Oprogramowanie USB Streamera (ESP32 Firmware)")
        flash_layout = QVBoxLayout(flash_box)

        flash_desc = QLabel(
            "Jeśli moduł posiada fabryczny firmware Skyloong, należy jednorazowo wgrać zoptymalizowane\n"
            "oprogramowanie USB Streamera, które odbiera klatki bezpośrednio przez USB."
        )
        flash_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        flash_layout.addWidget(flash_desc)

        flash_btn_row = QHBoxLayout()
        self.flash_btn = QPushButton("⚡ Wgraj firmware USB do modułu (1-klik)")
        self.flash_btn.setStyleSheet("""
            QPushButton {
                background: #7c3aed;
                color: #ffffff;
                font-weight: bold;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #8b5cf6;
            }
        """)
        self.flash_btn.clicked.connect(self.flash_firmware_dialog)
        flash_btn_row.addWidget(self.flash_btn, 2)

        self.build_btn = QPushButton("🔨 Przebuduj z kodu (PlatformIO)")
        self.build_btn.clicked.connect(self.rebuild_firmware)
        flash_btn_row.addWidget(self.build_btn, 1)
        flash_layout.addLayout(flash_btn_row)
        layout.addWidget(flash_box)

        layout.addStretch()
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Signals
        self.stream_ctrl.status_changed.connect(self.on_stream_status_changed)

    def refresh_ports(self):
        self.port_combo.clear()
        acm_ports = sorted(glob.glob('/dev/ttyACM*'))
        usb_ports = [p for p in sorted(glob.glob('/dev/ttyUSB*')) if p not in ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3']]
        ports = acm_ports + usb_ports
        if not ports:
            ports = ['/dev/ttyACM0']
        for p in ports:
            self.port_combo.addItem(p)

    def toggle_usb_connect(self):
        if self.stream_ctrl.connected:
            self.stop_streaming()
            self.stream_ctrl.disconnect_usb()
            self.connect_btn.setText("🔌 Połącz USB")
            self.status_lbl.setText("Status połączenia: ⚪ Rozłączony")
        else:
            port = self.port_combo.currentText()
            ok, msg = self.stream_ctrl.connect_usb(port=port)
            if ok:
                self.connect_btn.setText("❌ Rozłącz")
                self.status_lbl.setText(f"Status połączenia: 🟢 Połączono ({port})")
            else:
                QMessageBox.warning(self, "Błąd połączenia USB", f"Nie udało się połączyć z {port}:\n{msg}")

    def on_stream_status_changed(self, connected: bool, msg: str):
        if connected:
            self.status_lbl.setText(f"Status połączenia: 🟢 {msg}")
            self.connect_btn.setText("❌ Rozłącz")
        else:
            self.status_lbl.setText(f"Status połączenia: ⚪ {msg}")
            self.connect_btn.setText("🔌 Połącz USB")

    def toggle_streaming(self):
        if self.stream_thread and self.stream_thread.isRunning():
            self.stop_streaming()
        else:
            self.start_streaming()

    def start_streaming(self):
        if not self.stream_ctrl.connected:
            port = self.port_combo.currentText()
            ok, msg = self.stream_ctrl.connect_usb(port=port)
            if not ok:
                QMessageBox.warning(self, "Błąd USB", f"Najpierw podłącz port USB:\n{msg}")
                return

        self.stream_thread = USBStreamThread(
            controller=self.stream_ctrl,
            renderer_callback=self.get_current_frame_cb,
            target_fps=self.fps_slider.value(),
            quality=self.qual_slider.value()
        )
        self.stream_thread.fps_report.connect(self.on_fps_report)
        self.stream_thread.start()

        self.start_stream_btn.setText("⏹ Zatrzymaj Strumieniowanie USB")
        self.start_stream_btn.setStyleSheet("""
            QPushButton {
                background: #dc2626;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #ef4444;
            }
        """)
        self.streaming_toggled.emit(True)

    def stop_streaming(self):
        if self.stream_thread:
            self.stream_thread.stop()
            self.stream_thread = None

        self.start_stream_btn.setText("▶ Rozpocznij Strumieniowanie USB")
        self.start_stream_btn.setStyleSheet("""
            QPushButton {
                background: #059669;
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 10px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #10b981;
            }
        """)
        self.live_fps_lbl.setText("Rzeczywiste FPS: 0.0")
        self.live_bitrate_lbl.setText("Pasmo: 0.0 KB/s")
        self.live_latency_lbl.setText("Opóźnienie ACK: 0.0 ms")
        self.streaming_toggled.emit(False)

    def on_fps_changed(self, val):
        self.fps_val_lbl.setText(f"{val} FPS")
        if self.stream_thread:
            self.stream_thread.set_target_fps(val)

    def on_qual_changed(self, val):
        self.qual_val_lbl.setText(f"{val}%")
        if self.stream_thread:
            self.stream_thread.set_quality(val)

    def on_brightness_changed(self, val):
        pct = int((val / 255.0) * 100)
        self.bright_val_lbl.setText(f"{pct}%")
        if self.stream_ctrl.connected:
            self.stream_ctrl.set_brightness(val)

    def on_fps_report(self, fps: float, kbps: float, latency: float):
        self.live_fps_lbl.setText(f"Rzeczywiste FPS: {fps:.1f}")
        self.live_bitrate_lbl.setText(f"Pasmo: {kbps:.1f} KB/s")
        self.live_latency_lbl.setText(f"Opóźnienie ACK: {latency:.1f} ms")

    def flash_firmware_dialog(self):
        port = self.port_combo.currentText()
        reply = QMessageBox.question(
            self, "Wgrywanie oprogramowania USB",
            f"Czy chcesz wgrać zoptymalizowany firmware USB Streamera do modułu na porcie <b>{port}</b>?<br><br>"
            "Moduł zostanie zaprogramowany przez interfejs esptool.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        if self.stream_ctrl.connected:
            self.stop_streaming()
            self.stream_ctrl.disconnect_usb()

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        flash_script = os.path.join(base_dir, "usb_stream_firmware", "flash_firmware.py")

        dlg = QDialog(self)
        dlg.setWindowTitle("Wgrywanie Firmware ESP32-S3")
        dlg.resize(550, 350)
        d_layout = QVBoxLayout(dlg)

        info_lbl = QLabel(f"Wgrywanie firmware do {port}...")
        info_lbl.setStyleSheet("font-weight: bold; color: #00f0ff;")
        d_layout.addWidget(info_lbl)

        log_txt = QTextEdit()
        log_txt.setReadOnly(True)
        d_layout.addWidget(log_txt)

        close_btn = QPushButton("Zamknij")
        close_btn.setEnabled(False)
        close_btn.clicked.connect(dlg.accept)
        d_layout.addWidget(close_btn)

        dlg.show()

        def do_flash():
            try:
                proc = subprocess.Popen(
                    [sys.executable, flash_script, port],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                for line in proc.stdout:
                    log_txt.append(line.strip())
                proc.wait()
                if proc.returncode == 0:
                    log_txt.append("\n✅ SUKCES! Firmware został wgrany pomyślnie.")
                    info_lbl.setText("✅ Wgrywanie zakończone pomyślnie!")
                else:
                    log_txt.append(f"\n❌ Błąd wgrywania (kod {proc.returncode}).")
                    info_lbl.setText("❌ Błąd wgrywania.")
            except Exception as e:
                log_txt.append(f"\n❌ Wyjątek: {e}")
            finally:
                close_btn.setEnabled(True)

        QTimer.singleShot(100, do_flash)

    def rebuild_firmware(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        build_script = os.path.join(base_dir, "usb_stream_firmware", "build_and_flash.sh")
        
        QMessageBox.information(
            self, "Przebudowa Firmware",
            f"Kompilacja firmware zostanie uruchomiona za pomocą PlatformIO.\n"
            f"Możesz również uruchomić skrypt ręcznie:\n{build_script}"
        )
