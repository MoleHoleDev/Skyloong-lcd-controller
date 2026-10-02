import os
import sys
import time
import glob
import threading
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QStatusBar, QSystemTrayIcon, QMenu, QMessageBox,
    QPushButton, QGroupBox, QGridLayout, QScrollArea, QDialog,
    QSlider, QComboBox, QSplitter, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QAction, QPixmap, QImage

from lcd_core.config_manager import ConfigManager
from lcd_core.system_monitor import SystemMonitor
from lcd_core.screen_renderer import ScreenRenderer
from lcd_core.serial_controller import SerialController
from lcd_core.usb_streamer import USBStreamController, USBStreamThread

from ui.widgets.lcd_preview import LCDPreviewWidget
from ui.widgets.screen_gallery import ScreenGalleryWidget, SCREENS_CATALOG
from ui.widgets.retro_synthwave_panel import RetroSynthwavePanel
from ui.widgets.matrix_rain_panel import MatrixRainPanel
from ui.widgets.audio_visualizer_panel import AudioVisualizerPanel
from ui.widgets.dual_gauges_panel import DualGaugesPanel
from ui.widgets.pomodoro_panel import PomodoroPanel
from ui.widgets.scifi_terminal_panel import ScifiTerminalPanel
from ui.widgets.custom_tab import CustomTab
from ui.widgets.system_tab import SystemTab
from ui.widgets.clock_tab import ClockTab
from ui.widgets.calendar_tab import CalendarTab
from ui.widgets.image_tab import ImageTab
from ui.widgets.gif_tab import GifTab
from ui.widgets.slideshow_tab import SlideshowTab
from ui.theme import STYLE_SHEET


class MainWindow(QMainWindow):
    """
    Overhauled modern workstation for Skyloong GK104 Pro USB LCD Screen.
    Simple two-column layout: Left Screen Gallery + Live 320x240 LCD Preview,
    Right dedicated Screen Settings + USB Stream Control Engine.
    """

    def __init__(self, daemon_mode: bool = False):
        super().__init__()
        self.setWindowTitle("Skyloong LCD Controller — GK104 Pro Studio (320x240)")
        self.resize(1180, 780)
        self.setMinimumSize(960, 640)
        self.setStyleSheet(STYLE_SHEET)

        # Initialize Core Engines
        self.config_mgr = ConfigManager()
        self.monitor = SystemMonitor()
        self.renderer = ScreenRenderer(
            width=self.config_mgr.get("width", 320),
            height=self.config_mgr.get("height", 240)
        )
        self.serial_ctrl = SerialController(
            port=self.config_mgr.get("usb_stream_port", "/dev/ttyACM0"),
            baudrate=self.config_mgr.get("usb_stream_baud", 115200)
        )
        self.usb_stream_ctrl = USBStreamController(
            port=self.config_mgr.get("usb_stream_port", "/dev/ttyACM0"),
            baudrate=self.config_mgr.get("usb_stream_baud", 115200)
        )
        self.stream_thread: USBStreamThread = None

        self.current_metrics = self.monitor.get_all_metrics()
        self.fps_frame_counter = 0
        self.fps_timer_last = time.time()

        # Build UI
        self.setup_ui()
        self.setup_tray()

        # Timers
        # Render Loop (~30 FPS, 33ms)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.on_render_tick)
        self.render_timer.start(33)

        # Metrics collection (every 500ms)
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.on_metrics_tick)
        self.metrics_timer.start(500)

        # Auto-start USB streaming if enabled
        if self.config_mgr.get("usb_stream_auto_start", True):
            QTimer.singleShot(800, self.auto_start_usb_streaming)

        if daemon_mode:
            self.hide()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(10)

        # -------------------------------------------------------------
        # TOP GLOBAL BANNER & STREAM CONTROLLER
        # -------------------------------------------------------------
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #111827, stop:1 #0f172a);
                border: 1px solid #1e293b;
                border-radius: 8px;
            }
        """)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.setSpacing(12)

        # App Logo & Model Badge
        app_title = QLabel("⚡ SKYLOONG GK104 PRO")
        app_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00f0ff; letter-spacing: 0.5px;")
        top_layout.addWidget(app_title)

        sub_badge = QLabel("USB LCD 320×240")
        sub_badge.setStyleSheet("background: #0369a1; color: #ffffff; font-weight: bold; font-size: 10px; padding: 2px 6px; border-radius: 4px;")
        top_layout.addWidget(sub_badge)

        top_layout.addStretch()

        # USB Stream Status Pill
        self.stream_status_pill = QLabel("⚪ USB Stream: Rozłączony")
        self.stream_status_pill.setStyleSheet("color: #94a3b8; font-weight: bold; background: #0f172a; padding: 5px 10px; border-radius: 6px; border: 1px solid #1e293b;")
        top_layout.addWidget(self.stream_status_pill)

        # Brightness Slider
        bright_box = QHBoxLayout()
        bright_box.setSpacing(6)
        bright_box.addWidget(QLabel("☀️"))
        self.bright_slider = QSlider(Qt.Horizontal)
        self.bright_slider.setRange(10, 255)
        self.bright_slider.setValue(self.config_mgr.get("brightness", 200))
        self.bright_slider.setFixedWidth(100)
        self.bright_slider.valueChanged.connect(self.on_brightness_changed)
        bright_box.addWidget(self.bright_slider)
        top_layout.addLayout(bright_box)

        # Main Big Stream Toggle Button
        self.stream_toggle_btn = QPushButton("🚀 Rozpocznij Strumieniowanie USB")
        self.stream_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.stream_toggle_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #34d399;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
            }
        """)
        self.stream_toggle_btn.clicked.connect(self.toggle_usb_streaming)
        top_layout.addWidget(self.stream_toggle_btn)

        # Flasher / Tools Button
        self.tools_btn = QPushButton("⚙️ Opcje / Flash")
        self.tools_btn.setStyleSheet("background: #1e293b; color: #94a3b8; font-size: 11px; padding: 6px 10px;")
        self.tools_btn.clicked.connect(self.open_flasher_dialog)
        top_layout.addWidget(self.tools_btn)

        main_layout.addWidget(top_bar)

        # -------------------------------------------------------------
        # MAIN 2-COLUMN WORKSPACE
        # -------------------------------------------------------------
        split_layout = QHBoxLayout()
        split_layout.setSpacing(14)

        # =============================================================
        # LEFT COLUMN: Live Preview (Top) + Screen Gallery (Bottom)
        # =============================================================
        left_col = QWidget()
        left_layout = QVBoxLayout(left_col)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 1. Live Virtual LCD Preview (320x240)
        preview_box = QFrame()
        preview_box.setStyleSheet("background: #111827; border: 1px solid #1e293b; border-radius: 8px; padding: 6px;")
        preview_box_layout = QVBoxLayout(preview_box)
        preview_box_layout.setContentsMargins(8, 8, 8, 8)
        preview_box_layout.setSpacing(8)

        self.lcd_preview = LCDPreviewWidget()
        preview_box_layout.addWidget(self.lcd_preview)

        # Quick toolbar under preview
        quick_tools = QHBoxLayout()
        self.active_mode_lbl = QLabel("Aktywny: Retro Synthwave")
        self.active_mode_lbl.setStyleSheet("color: #00f0ff; font-weight: bold; font-size: 12px;")
        quick_tools.addWidget(self.active_mode_lbl)

        quick_tools.addStretch()

        self.switch_raw_btn = QPushButton("⚡ Przełącznik fabryczny (USB `)")
        self.switch_raw_btn.setToolTip("Wysyła sygnał '`' po USB CDC do modułu")
        self.switch_raw_btn.setStyleSheet("background: #1e293b; color: #94a3b8; font-size: 10px; padding: 4px 8px;")
        self.switch_raw_btn.clicked.connect(self.send_usb_backtick_switch)
        quick_tools.addWidget(self.switch_raw_btn)

        preview_box_layout.addLayout(quick_tools)
        left_layout.addWidget(preview_box)

        # 2. Screen Gallery
        self.gallery = ScreenGalleryWidget(current_mode=self.config_mgr.get("current_mode", "retro_synthwave"))
        self.gallery.screen_changed.connect(self.on_screen_selected)
        left_layout.addWidget(self.gallery, 1)

        split_layout.addWidget(left_col, 56)

        # =============================================================
        # RIGHT COLUMN: Dedicated Screen Settings & USB Device Controls
        # =============================================================
        right_col = QWidget()
        right_layout = QVBoxLayout(right_col)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # Settings Container Card
        settings_card = QFrame()
        settings_card.setStyleSheet("background: #111827; border: 1px solid #1e293b; border-radius: 8px;")
        settings_card_layout = QVBoxLayout(settings_card)
        settings_card_layout.setContentsMargins(12, 10, 12, 10)
        settings_card_layout.setSpacing(10)

        # Header of right column
        self.settings_header_lbl = QLabel("⚙️ Ustawienia ekranu")
        self.settings_header_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        settings_card_layout.addWidget(self.settings_header_lbl)

        # Stack of individual screen settings panels
        self.settings_stack = QStackedWidget()
        self.panels = {}

        # 0: retro_synthwave
        self.panels["retro_synthwave"] = RetroSynthwavePanel(self.config_mgr)
        self.panels["retro_synthwave"].settings_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["retro_synthwave"])

        # 1: matrix_rain
        self.panels["matrix_rain"] = MatrixRainPanel(self.config_mgr)
        self.panels["matrix_rain"].settings_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["matrix_rain"])

        # 2: audio_visualizer
        self.panels["audio_visualizer"] = AudioVisualizerPanel(self.config_mgr)
        self.panels["audio_visualizer"].settings_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["audio_visualizer"])

        # 3: dual_gauges
        self.panels["dual_gauges"] = DualGaugesPanel(self.config_mgr)
        self.panels["dual_gauges"].settings_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["dual_gauges"])

        # 4: pomodoro
        self.panels["pomodoro"] = PomodoroPanel(self.config_mgr)
        self.panels["pomodoro"].settings_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["pomodoro"])

        # 5: scifi_terminal
        self.panels["scifi_terminal"] = ScifiTerminalPanel(self.config_mgr)
        self.panels["scifi_terminal"].settings_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["scifi_terminal"])

        # 6: custom
        self.panels["custom"] = CustomTab(self.config_mgr)
        self.panels["custom"].config_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["custom"])

        # 7: usage
        self.panels["usage"] = SystemTab(self.config_mgr)
        self.panels["usage"].config_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["usage"])

        # 8: temperatures
        self.panels["temperatures"] = self.panels["usage"]  # Shared telemetry settings

        # 9: clock
        self.panels["clock"] = ClockTab(self.config_mgr)
        self.panels["clock"].config_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["clock"])

        # 10: calendar
        self.panels["calendar"] = CalendarTab(self.config_mgr)
        self.panels["calendar"].config_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["calendar"])

        # 11: image
        self.panels["image"] = ImageTab(self.config_mgr)
        self.panels["image"].config_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["image"])

        # 12: gif
        self.panels["gif"] = GifTab(self.config_mgr)
        self.panels["gif"].config_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["gif"])

        # 13: slideshow
        self.panels["slideshow"] = SlideshowTab(self.config_mgr)
        self.panels["slideshow"].config_changed.connect(self.on_settings_modified)
        self.settings_stack.addWidget(self.panels["slideshow"])

        settings_card_layout.addWidget(self.settings_stack, 1)
        right_layout.addWidget(settings_card, 1)

        # Bottom Stream Param Toolbar
        stream_params_card = QFrame()
        stream_params_card.setStyleSheet("background: #0f172a; border: 1px solid #1e293b; border-radius: 8px;")
        sp_layout = QVBoxLayout(stream_params_card)
        sp_layout.setContentsMargins(10, 8, 10, 8)
        sp_layout.setSpacing(6)

        sp_header = QLabel("⚡ Parametry Strumienia USB")
        sp_header.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px;")
        sp_layout.addWidget(sp_header)

        params_row = QHBoxLayout()
        params_row.setSpacing(10)

        # Port Selector
        params_row.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.refresh_ports_list()
        self.port_combo.currentIndexChanged.connect(self.on_port_changed)
        params_row.addWidget(self.port_combo, 1)

        # Refresh Ports Button
        refresh_ports_btn = QPushButton("🔄")
        refresh_ports_btn.setFixedWidth(30)
        refresh_ports_btn.setStyleSheet("padding: 4px;")
        refresh_ports_btn.clicked.connect(self.refresh_ports_list)
        params_row.addWidget(refresh_ports_btn)

        # FPS Selector
        params_row.addWidget(QLabel("FPS:"))
        self.fps_combo = QComboBox()
        for f in [15, 30, 45, 60]:
            self.fps_combo.addItem(f"{f} FPS", f)
        cur_fps = self.config_mgr.get("usb_stream_fps", 30)
        idx_f = [15, 30, 45, 60].index(cur_fps) if cur_fps in [15, 30, 45, 60] else 1
        self.fps_combo.setCurrentIndex(idx_f)
        self.fps_combo.currentIndexChanged.connect(self.on_stream_fps_changed)
        params_row.addWidget(self.fps_combo)

        # Quality
        params_row.addWidget(QLabel("Jakość:"))
        self.quality_combo = QComboBox()
        for q in [70, 80, 85, 90, 95]:
            self.quality_combo.addItem(f"{q}%", q)
        cur_q = self.config_mgr.get("usb_stream_quality", 85)
        idx_q = [70, 80, 85, 90, 95].index(cur_q) if cur_q in [70, 80, 85, 90, 95] else 2
        self.quality_combo.setCurrentIndex(idx_q)
        self.quality_combo.currentIndexChanged.connect(self.on_stream_quality_changed)
        params_row.addWidget(self.quality_combo)

        sp_layout.addLayout(params_row)
        right_layout.addWidget(stream_params_card)

        split_layout.addWidget(right_col, 44)
        main_layout.addLayout(split_layout, 1)

        # -------------------------------------------------------------
        # STATUS BAR
        # -------------------------------------------------------------
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.sb_stats_lbl = QLabel("CPU: 0% | RAM: 0% | GPU: 0%")
        self.sb_stats_lbl.setStyleSheet("color: #94a3b8; font-weight: 500;")
        self.status_bar.addWidget(self.sb_stats_lbl, 1)

        self.sb_stream_lbl = QLabel("⚡ USB Engine: Ready")
        self.sb_stream_lbl.setStyleSheet("color: #10b981; font-weight: bold; margin-right: 12px;")
        self.status_bar.addPermanentWidget(self.sb_stream_lbl)

        # Set initial screen
        self.on_screen_selected(self.config_mgr.get("current_mode", "retro_synthwave"))

    def on_screen_selected(self, mode_id: str):
        """Switches active rendering mode and opens the corresponding settings panel."""
        self.config_mgr.set("current_mode", mode_id)
        
        # Find screen title
        title = mode_id
        for s in SCREENS_CATALOG:
            if s["id"] == mode_id:
                title = f"{s['icon']} {s['title']}"
                break

        self.active_mode_lbl.setText(f"Aktywny: {title}")
        self.settings_header_lbl.setText(f"⚙️ Ustawienia: {title}")

        # Switch stack panel
        panel = self.panels.get(mode_id)
        if panel and self.settings_stack.indexOf(panel) >= 0:
            self.settings_stack.setCurrentWidget(panel)

    def on_settings_modified(self):
        """Triggered when any settings panel changes a value."""
        pass

    def on_render_tick(self):
        """Renders current frame and updates preview & streamer."""
        try:
            cfg = self.config_mgr.config
            img = self.renderer.render(cfg, self.current_metrics)
            mode_id = cfg.get("current_mode", "custom")
            
            # Update virtual preview
            self.lcd_preview.update_frame(img, mode_id)

            # FPS counter
            self.fps_frame_counter += 1
            now = time.time()
            if now - self.fps_timer_last >= 1.0:
                fps = self.fps_frame_counter / (now - self.fps_timer_last)
                self.lcd_preview.fps_lbl.setText(f"{fps:.0f} FPS")
                self.fps_frame_counter = 0
                self.fps_timer_last = now

        except Exception as e:
            print(f"[MainWindow] Render tick error: {e}")

    def on_metrics_tick(self):
        """Polls hardware sensors."""
        self.current_metrics = self.monitor.get_all_metrics()
        
        # Update system tab live gauges if present
        if "usage" in self.panels:
            self.panels["usage"].update_live_metrics(self.current_metrics)

        cpu = self.current_metrics.get('cpu_percent', 0.0)
        ram = self.current_metrics.get('ram_percent', 0.0)
        gpu = self.current_metrics.get('gpu_percent', 0.0)
        cpu_t = self.current_metrics.get('cpu_temp', 0.0)
        
        self.sb_stats_lbl.setText(f"CPU: {cpu:.0f}% ({cpu_t:.0f}°C) | RAM: {ram:.0f}% | GPU: {gpu:.0f}%")

    def toggle_usb_streaming(self):
        """Starts or stops the USB DMA streamer."""
        if self.stream_thread and self.stream_thread.isRunning():
            self.stop_usb_streaming()
        else:
            self.start_usb_streaming()

    def start_usb_streaming(self):
        port = self.port_combo.currentText()
        if not port or not os.path.exists(port):
            self.refresh_ports_list()
            port = self.port_combo.currentText()

        if not port or not os.path.exists(port):
            QMessageBox.warning(self, "Brak portu USB", f"Nie wykryto urządzenia USB pod adresem '{port}'.\nUpewnij się, że ekran jest podłączony kablem USB-C do komputera.")
            return

        fps = self.fps_combo.currentData() or 30
        quality = self.quality_combo.currentData() or 85

        if self.stream_thread and self.stream_thread.isRunning():
            self.stream_thread.stop()

        self.stream_thread = USBStreamThread(
            controller=self.usb_stream_ctrl,
            renderer_callback=lambda: self.renderer.get_current_frame(),
            fps=fps,
            quality=quality,
            port=port
        )
        self.stream_thread.stats_updated.connect(self.on_stream_stats_updated)
        self.stream_thread.error_occurred.connect(self.on_stream_error)
        self.stream_thread.start()

        # Update UI buttons
        self.stream_toggle_btn.setText("⏹ Zatrzymaj Strumieniowanie USB")
        self.stream_toggle_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #dc2626, stop:1 #ef4444);
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #f87171;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #b91c1c, stop:1 #dc2626);
            }
        """)
        self.stream_status_pill.setText(f"🟢 USB Stream: {port} (Aktywny)")
        self.stream_status_pill.setStyleSheet("color: #10b981; font-weight: bold; background: #0f172a; padding: 5px 10px; border-radius: 6px; border: 1px solid #10b981;")
        self.sb_stream_lbl.setText(f"⚡ USB Streaming: 🟢 {fps} FPS")

    def stop_usb_streaming(self):
        if self.stream_thread:
            self.stream_thread.stop()
            self.stream_thread = None

        self.usb_stream_ctrl.disconnect_usb()

        self.stream_toggle_btn.setText("🚀 Rozpocznij Strumieniowanie USB")
        self.stream_toggle_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #059669, stop:1 #10b981);
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px 16px;
                border-radius: 6px;
                border: 1px solid #34d399;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669);
            }
        """)
        self.stream_status_pill.setText("⚪ USB Stream: Rozłączony")
        self.stream_status_pill.setStyleSheet("color: #94a3b8; font-weight: bold; background: #0f172a; padding: 5px 10px; border-radius: 6px; border: 1px solid #1e293b;")
        self.sb_stream_lbl.setText("⚡ USB Stream: ⚪ Rozłączony")

    def auto_start_usb_streaming(self):
        self.refresh_ports_list()
        port = self.port_combo.currentText()
        if port and os.path.exists(port):
            self.start_usb_streaming()

    def on_stream_stats_updated(self, fps: float, kbps: float):
        self.stream_status_pill.setText(f"🟢 USB: {fps:.0f} FPS • {kbps:.0f} KB/s")

    def on_stream_error(self, err: str):
        self.sb_stream_lbl.setText(f"❌ USB Błąd: {err[:30]}")
        self.stop_usb_streaming()

    def on_brightness_changed(self, val: int):
        self.config_mgr.set("brightness", val)
        if self.usb_stream_ctrl.is_open:
            self.usb_stream_ctrl.set_brightness(val)
        else:
            # Send brightness setting even if not streaming continuously
            port = self.port_combo.currentText()
            if port and os.path.exists(port):
                self.usb_stream_ctrl.connect_usb(port)
                self.usb_stream_ctrl.set_brightness(val)

    def on_port_changed(self):
        port = self.port_combo.currentText()
        if port:
            self.config_mgr.set("usb_stream_port", port)
            self.usb_stream_ctrl.port = port
            self.serial_ctrl.port = port

    def on_stream_fps_changed(self):
        fps = self.fps_combo.currentData() or 30
        self.config_mgr.set("usb_stream_fps", fps)
        if self.stream_thread:
            self.stream_thread.set_target_fps(fps)

    def on_stream_quality_changed(self):
        q = self.quality_combo.currentData() or 85
        self.config_mgr.set("usb_stream_quality", q)
        if self.stream_thread:
            self.stream_thread.set_quality(q)

    def refresh_ports_list(self):
        self.port_combo.blockSignals(True)
        self.port_combo.clear()
        acm_ports = sorted(glob.glob("/dev/ttyACM*"))
        usb_ports = sorted(glob.glob("/dev/ttyUSB*"))
        all_ports = acm_ports + usb_ports
        for p in all_ports:
            self.port_combo.addItem(p)
        if not all_ports:
            self.port_combo.addItem("/dev/ttyACM0")
        
        cur = self.config_mgr.get("usb_stream_port", "")
        idx = self.port_combo.findText(cur)
        if idx >= 0:
            self.port_combo.setCurrentIndex(idx)
        elif acm_ports:
            # Pick highest ACM port by default
            self.port_combo.setCurrentIndex(self.port_combo.findText(acm_ports[-1]))
        else:
            self.port_combo.setCurrentIndex(0)
            
        self.port_combo.blockSignals(False)
        self.on_port_changed()

    def send_usb_backtick_switch(self):
        port = self.port_combo.currentText()
        success, msg = self.serial_ctrl.switch_app(port=port)
        if success:
            self.statusBar().showMessage("✅ Wysłano sygnał przełączenia USB (`) do ekranu", 3000)
        else:
            self.statusBar().showMessage(f"❌ {msg}", 4000)

    def open_flasher_dialog(self):
        """Opens dedicated USB firmware flash dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("⚡ Flasher Firmware ESP32-S3 (PlatformIO / USB)")
        dialog.resize(520, 360)
        d_layout = QVBoxLayout(dialog)

        info = QLabel(
            "<h3>Flasher Firmware USB Streamer (320x240 DMA)</h3>"
            "<p>Wgraj lub zaktualizuj wsad PlatformIO na układzie ESP32-S3 modułu ekranu Skyloong GK104 Pro.</p>"
            "<ul>"
            "<li>Rozdzielczość: <b>320x240 ST7789 SPI DMA</b></li>"
            "<li>Dekoder: <b>TJpgDec sprzętowy</b></li>"
            "<li>Prędkość: <b>do 60 FPS przez USB CDC</b></li>"
            "</ul>"
        )
        info.setTextFormat(Qt.RichText)
        info.setWordWrap(True)
        d_layout.addWidget(info)

        flash_btn = QPushButton("⚡ Wgraj Firmware do modułu (1-Klik)")
        flash_btn.setStyleSheet("background: #0284c7; color: white; font-weight: bold; font-size: 13px; padding: 10px;")
        
        status_lbl = QLabel("Gotowy do wgrania.")
        status_lbl.setStyleSheet("color: #94a3b8;")

        def do_flash():
            flash_btn.setEnabled(False)
            status_lbl.setText("Wgrywanie firmware przez esptool... Czekaj...")
            
            # Run flash script
            flash_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "usb_stream_firmware", "flash_firmware.py")
            import subprocess
            res = subprocess.run([sys.executable, flash_script], capture_output=True, text=True)
            flash_btn.setEnabled(True)
            if res.returncode == 0:
                status_lbl.setText("✅ Firmware pomyślnie wgrany!")
                QMessageBox.information(dialog, "Sukces", "Firmware został pomyślnie wgrany do modułu ESP32-S3!\nEkran jest gotowy do streamingu.")
            else:
                status_lbl.setText(f"❌ Błąd wgrywania: {res.stderr[:60]}")
                QMessageBox.critical(dialog, "Błąd", f"Wgrywanie nie powiodło się:\n{res.stderr}")

        flash_btn.clicked.connect(do_flash)
        d_layout.addWidget(flash_btn)
        d_layout.addWidget(status_lbl)
        d_layout.addStretch()

        close_btn = QPushButton("Zamknij")
        close_btn.clicked.connect(dialog.accept)
        d_layout.addWidget(close_btn)

        dialog.exec()

    def setup_tray(self):
        """Configures system tray icon."""
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.windowIcon() if not self.windowIcon().isNull() else QIcon.fromTheme("video-display"))

        tray_menu = QMenu()
        show_action = QAction("Pokaż okno", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)

        stream_action = QAction("Włącz / Wyłącz Stream USB", self)
        stream_action.triggered.connect(self.toggle_usb_streaming)
        tray_menu.addAction(stream_action)

        tray_menu.addSeparator()

        quit_action = QAction("Zakończ", self)
        quit_action.triggered.connect(self.close_app)
        tray_menu.addAction(quit_action)

        self.tray.setContextMenu(tray_menu)
        self.tray.show()

    def closeEvent(self, event):
        """Stop threads on window close."""
        if self.stream_thread:
            self.stream_thread.stop()
        self.config_mgr.save()
        event.accept()

    def close_app(self):
        if self.stream_thread:
            self.stream_thread.stop()
        self.config_mgr.save()
        sys.exit(0)
