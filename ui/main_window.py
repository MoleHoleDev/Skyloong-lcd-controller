import os
import sys
import time
import threading
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QLabel, QStatusBar, QSystemTrayIcon, QMenu, QMessageBox,
    QPushButton, QGroupBox, QGridLayout, QScrollArea, QDialog, QTextBrowser,
    QCheckBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction, QPixmap, QImage

from lcd_core.config_manager import ConfigManager
from lcd_core.system_monitor import SystemMonitor
from lcd_core.screen_renderer import ScreenRenderer
from lcd_core.network_server import NetworkServer
from lcd_core.serial_controller import SerialController
from lcd_core.esp_manager import ESPManager
from lcd_core.http_controller import HTTPController

from ui.widgets.lcd_preview import LCDPreviewWidget
from ui.widgets.image_tab import ImageTab
from ui.widgets.gif_tab import GifTab
from ui.widgets.slideshow_tab import SlideshowTab
from ui.widgets.clock_tab import ClockTab
from ui.widgets.calendar_tab import CalendarTab
from ui.widgets.system_tab import SystemTab
from ui.widgets.custom_tab import CustomTab
from ui.widgets.settings_tab import SettingsTab
from ui.theme import STYLE_SHEET

class MainWindow(QMainWindow):
    """
    Main application window for Skyloong LCD Controller.
    """

    def __init__(self, daemon_mode: bool = False):
        super().__init__()
        self.setWindowTitle("Skyloong LCD Controller — GK104 Pro Studio")
        self.resize(1080, 720)
        self.setMinimumSize(860, 580)
        self.setStyleSheet(STYLE_SHEET)

        # Initialize Logic & Core Engines
        self.config_mgr = ConfigManager()
        self.monitor = SystemMonitor()
        self.renderer = ScreenRenderer(
            width=self.config_mgr.get("width", 240),
            height=self.config_mgr.get("height", 240)
        )
        self.net_server = NetworkServer(
            host=self.config_mgr.get("tcp_host", "0.0.0.0"),
            port=self.config_mgr.get("tcp_port", 1648)
        )
        self.net_server.metrics_getter = self.monitor.get_all_metrics

        self.serial_ctrl = SerialController(
            port=self.config_mgr.get("serial_port", "/dev/ttyACM0"),
            baudrate=self.config_mgr.get("serial_baudrate", 115200)
        )
        self.http_ctrl = HTTPController(
            screen_ip=self.config_mgr.get("screen_ip", "192.168.1.115")
        )

        # Performance / FPS measurement
        self.frame_count = 0
        self.fps_last_time = time.time()
        self.current_metrics = self.monitor.get_all_metrics()
        self.is_sending_frame = False

        # Build UI
        self.setup_ui()
        self.setup_tray()

        # Start Telemetry & Rendering Timers
        # Render Loop at ~30 FPS (33ms)
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self.on_render_tick)
        self.render_timer.start(33)

        # Metrics collection every 500ms
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self.on_metrics_tick)
        self.metrics_timer.start(500)

        # Live Wi-Fi Sync Timer (e.g. 2000ms)
        self.sync_timer = QTimer(self)
        self.sync_timer.timeout.connect(self.on_sync_tick)

        # Autostart TCP server if enabled
        if self.config_mgr.get("tcp_server_enabled", True):
            self.net_server.start()

        if daemon_mode:
            self.hide()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(12)

        # Left / Middle Pane: Tabs for features
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setUsesScrollButtons(True)

        # 1. Custom / Hybrid Dashboard ("Do wyboru")
        self.custom_tab = CustomTab(self.config_mgr)
        self.custom_tab.config_changed.connect(self.on_config_updated)
        self.tabs.addTab(self.custom_tab, "🧩 Do wyboru")

        # 2. System Usage & Temperatures
        self.system_tab = SystemTab(self.config_mgr)
        self.system_tab.config_changed.connect(self.on_config_updated)
        self.tabs.addTab(self.system_tab, "📊 Zużycie i Temp")

        # 3. Clock Tab
        self.clock_tab = ClockTab(self.config_mgr)
        self.clock_tab.config_changed.connect(self.on_config_updated)
        self.tabs.addTab(self.clock_tab, "🕒 Zegar")

        # 4. Calendar Tab
        self.calendar_tab = CalendarTab(self.config_mgr)
        self.calendar_tab.config_changed.connect(self.on_config_updated)
        self.tabs.addTab(self.calendar_tab, "📅 Kalendarz")

        # 5. Image Tab
        self.image_tab = ImageTab(self.config_mgr)
        self.image_tab.config_changed.connect(self.on_config_updated)
        self.tabs.addTab(self.image_tab, "🖼️ Zdjęcia")

        # 6. GIF Tab
        self.gif_tab = GifTab(self.config_mgr)
        self.gif_tab.config_changed.connect(self.on_config_updated)
        self.tabs.addTab(self.gif_tab, "🎞️ GIFy")

        # 7. Slideshow Tab
        self.slideshow_tab = SlideshowTab(self.config_mgr)
        self.slideshow_tab.config_changed.connect(self.on_config_updated)
        self.tabs.addTab(self.slideshow_tab, "📋 Pokaz slajdów")

        # 8. Settings & Connections Tab
        self.settings_tab = SettingsTab(self.config_mgr, self.net_server, self.serial_ctrl, self.http_ctrl)
        self.settings_tab.config_changed.connect(self.on_config_updated)
        self.tabs.addTab(self.settings_tab, "⚙️ Ustawienia")

        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs, stretch=3)

        # Right Pane: LCD Preview Box & Mode Switch Controller
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(10)

        self.preview_widget = LCDPreviewWidget()
        right_panel.addWidget(self.preview_widget)

        # Mode Controller Group
        mode_box = QGroupBox("🎮 Sterowanie & Wybór trybu ekranu")
        mode_box_layout = QVBoxLayout(mode_box)
        mode_box_layout.setContentsMargins(10, 10, 10, 10)
        mode_box_layout.setSpacing(8)

        # Active Mode Banner
        self.active_mode_lbl = QLabel("🟢 Aktywny na żywo: 🧩 Do wyboru")
        self.active_mode_lbl.setStyleSheet(
            "font-weight: bold; color: #00f0ff; background: #0f172a; padding: 6px 10px; border-radius: 6px; border: 1px solid #1e293b; font-size: 12px;"
        )
        self.active_mode_lbl.setAlignment(Qt.AlignCenter)
        mode_box_layout.addWidget(self.active_mode_lbl)

        # Quick Mode Buttons Grid
        grid = QGridLayout()
        grid.setSpacing(6)

        mode_buttons = [
            ("🧩 Hybryda", "custom", 0),
            ("📊 Zużycie", "usage", 1),
            ("🕒 Zegar", "clock", 2),
            ("📅 Kalendarz", "calendar", 3),
            ("🖼️ Zdjęcie", "image", 4),
            ("🎞️ Animacja GIF", "gif", 5),
            ("📋 Pokaz slajdów", "slideshow", 6),
        ]

        for i, (label, mode_key, tab_idx) in enumerate(mode_buttons):
            row = i // 2
            col = i % 2
            btn = QPushButton(label)
            btn.setStyleSheet("font-size: 11px; padding: 6px 8px;")
            btn.clicked.connect(lambda _, m=mode_key, t=tab_idx: self.switch_to_mode(m, t))
            if i == len(mode_buttons) - 1 and col == 0:
                grid.addWidget(btn, row, col, 1, 2)
            else:
                grid.addWidget(btn, row, col)

        mode_box_layout.addLayout(grid)

        # Push To Screen Button
        self.push_to_screen_btn = QPushButton("📡 Wyślij widok na ekran (Wi-Fi)")
        self.push_to_screen_btn.setObjectName("AccentButton")
        self.push_to_screen_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #06b6d4);
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
                padding: 8px;
                border-radius: 6px;
                border: 1px solid #38bdf8;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #0891b2);
            }
        """)
        self.push_to_screen_btn.clicked.connect(lambda: self.send_current_view_to_screen(silent=False))
        mode_box_layout.addWidget(self.push_to_screen_btn)

        # Live Sync Checkbox
        self.live_sync_cb = QCheckBox("🔄 Ciągła synchronizacja na żywo (co 2s)")
        self.live_sync_cb.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 11px; padding: 2px;")
        self.live_sync_cb.toggled.connect(self.on_live_sync_toggled)
        mode_box_layout.addWidget(self.live_sync_cb)

        # Quick USB Switch Button
        self.usb_quick_switch_btn = QPushButton("⚡ Przełącz ekran fizyczny (USB `)")
        self.usb_quick_switch_btn.setToolTip("Wysyła sygnał '`' (backtick) bezpośrednio przez kabel USB (/dev/ttyACM*), co natychmiast przełącza ekran na następną aplikację (Zegar -> APS -> GIF -> Pogoda -> Sysinfo).")
        self.usb_quick_switch_btn.setStyleSheet("""
            QPushButton {
                background: #0f172a;
                color: #38bdf8;
                font-weight: bold;
                font-size: 11px;
                padding: 6px;
                border-radius: 6px;
                border: 1px solid #0284c7;
            }
            QPushButton:hover {
                background: #0284c7;
                color: #ffffff;
            }
        """)
        self.usb_quick_switch_btn.clicked.connect(self.on_usb_quick_switch)
        mode_box_layout.addWidget(self.usb_quick_switch_btn)

        # Apply Current Tab Button
        self.apply_btn = QPushButton("🚀 Ustaw obecną zakładkę jako aktywną")
        self.apply_btn.clicked.connect(self.apply_current_tab_mode)
        mode_box_layout.addWidget(self.apply_btn)

        # Guide Dialog Button
        self.guide_btn = QPushButton("📖 Jak przełączać tryb na ekraniku GK104?")
        self.guide_btn.setStyleSheet("background: #0f172a; border: 1px solid #334155; font-size: 11px; padding: 5px;")
        self.guide_btn.clicked.connect(self.show_screen_guide)
        mode_box_layout.addWidget(self.guide_btn)

        right_panel.addWidget(mode_box)
        right_panel.addStretch()
        main_layout.addLayout(right_panel, stretch=2)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.sb_stats_lbl = QLabel("CPU: 0% | RAM: 0% | GPU: 0% | Temp: --°C")
        self.sb_stats_lbl.setStyleSheet("color: #94a3b8; font-weight: 500;")
        self.status_bar.addWidget(self.sb_stats_lbl, 1)

        self.sb_net_lbl = QLabel("🌐 TCP: Port 1648 (Aktywny)")
        self.sb_net_lbl.setStyleSheet("color: #10b981; font-weight: bold;")
        self.status_bar.addPermanentWidget(self.sb_net_lbl)

        # Set initial tab according to config
        mode_to_tab = {
            "custom": 0,
            "usage": 1,
            "temperatures": 1,
            "clock": 2,
            "calendar": 3,
            "image": 4,
            "gif": 5,
            "slideshow": 6
        }
        initial_mode = self.config_mgr.get("current_mode", "custom")
        if initial_mode in mode_to_tab:
            self.tabs.setCurrentIndex(mode_to_tab[initial_mode])
        self.update_active_mode_badge(initial_mode)

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        # Default placeholder icon or custom
        pix = QPixmap(32, 32)
        pix.fill(Qt.transparent)
        self.tray_icon.setIcon(QIcon(pix))

        tray_menu = QMenu()
        show_action = QAction("Otwórz panel sterowania", self)
        show_action.triggered.connect(self.show_and_activate)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()
        quit_action = QAction("Zakończ program", self)
        quit_action.triggered.connect(self.close_application)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tab_changed(self, index: int):
        tab_to_mode = {
            0: "custom",
            1: "usage",
            2: "clock",
            3: "calendar",
            4: "image",
            5: "gif",
            6: "slideshow",
            7: self.config_mgr.get("current_mode", "custom")
        }
        if index in tab_to_mode and index != 7:
            new_mode = tab_to_mode[index]
            self.config_mgr.set("current_mode", new_mode)
            self.update_active_mode_badge(new_mode)

    def switch_to_mode(self, mode_key: str, tab_idx: int):
        """Switches both the current tab and active rendering mode."""
        self.tabs.setCurrentIndex(tab_idx)
        self.config_mgr.set("current_mode", mode_key)
        self.update_active_mode_badge(mode_key)

    def apply_current_tab_mode(self):
        """Applies mode corresponding to current selected tab."""
        idx = self.tabs.currentIndex()
        self.on_tab_changed(idx)
        QMessageBox.information(
            self,
            "Aktywacja trybu",
            f"Aktywowano widok: <b>{self.config_mgr.get('current_mode', 'custom').upper()}</b>!<br>"
            "Ekran oraz podgląd na żywo wyświetlają teraz wybrany szablon."
        )

    def update_active_mode_badge(self, mode_key: str):
        mode_names = {
            "custom": "🧩 Do wyboru (Hybryda)",
            "usage": "📊 Zużycie & Temp",
            "clock": "🕒 Zegar",
            "calendar": "📅 Kalendarz",
            "image": "🖼️ Zdjęcia",
            "gif": "🎞️ GIFy",
            "slideshow": "📋 Pokaz slajdów",
            "temperatures": "🌡️ Temperatury"
        }
        name = mode_names.get(mode_key, mode_key.capitalize())
        self.active_mode_lbl.setText(f"🟢 Aktywny na żywo: {name}")

    def on_usb_quick_switch(self):
        """Sends backtick over USB to switch to next screen app."""
        ok, msg = self.serial_ctrl.switch_app()
        if ok:
            self.usb_quick_switch_btn.setText("✅ Przełączono (USB)")
            self.statusBar().showMessage("Wysłano sygnał zmiany trybu ekranu przez kabel USB (`)...", 3000)
        else:
            self.usb_quick_switch_btn.setText("⚠️ Błąd USB")
            self.statusBar().showMessage(f"Błąd USB: {msg}", 4000)
            QMessageBox.warning(self, "Błąd przełączania USB", f"Nie udało się wysłać sygnału przez USB:\n{msg}\n\nUpewnij się, że moduł ekranu jest wpięty kablem USB do komputera.")
        QTimer.singleShot(2000, lambda: self.usb_quick_switch_btn.setText("⚡ Przełącz ekran fizyczny (USB `)"))

    def show_screen_guide(self):
        """Displays visual guide on how to switch physical GK104 Pro screen modes."""
        ips = ESPManager.get_pc_network_ips()
        primary_ip = ips[0]['ip'] if ips else "192.168.1.173"

        dlg = QDialog(self)
        dlg.setWindowTitle("Instrukcja: Przełączanie trybów na ekranie Skyloong GK104 Pro")
        dlg.resize(640, 560)
        dlg.setStyleSheet(STYLE_SHEET)

        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(14, 14, 14, 14)
        dlg_layout.setSpacing(12)

        tb = QTextBrowser()
        tb.setOpenExternalLinks(False)
        tb.setStyleSheet("""
            QTextBrowser {
                background-color: #0f172a;
                color: #e2e8f0;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.5;
            }
        """)

        html_content = f"""
        <h3 style="color: #00f0ff; margin-top:0;">🎮 Jak przełączać tryby na fizycznym ekranie Skyloong GK104 Pro?</h3>
        
        <p>Ekran klawiatury to moduł <b>ESP32-S3</b>, który posiada kilka wbudowanych trybów pracy (Zegar &rarr; APS &rarr; GIF &rarr; Pogoda &rarr; PC Monitor). Poniżej sposoby sterowania:</p>

        <h4 style="color: #38bdf8;">1. Bezpośrednio z programu przez kabel USB (Najwygodniejsza metoda):</h4>
        <ul>
            <li>Kliknij przycisk <b>⚡ Przełącz ekran fizyczny (USB `)</b> na bocznym panelu programu lub w zakładce <i>Ustawienia</i>.</li>
            <li>Aplikacja wyśle znak <code>`</code> (backtick) bezpośrednio przez port szeregowy USB (<code>/dev/ttyACM*</code>), co natychmiast przełączy ekran na kolejną aplikację bez dotykania klawiatury!</li>
        </ul>

        <h4 style="color: #38bdf8;">2. Skrót klawiszowy na klawiaturze (gdy ekran jest wpięty w slot):</h4>
        <ul>
            <li>Naciśnij kombinację <b>Fn + ~</b> (Fn + tylda obok klawisza 1).</li>
            <li>Każde naciśnięcie przeskakuje do kolejnego widoku w karuzeli.</li>
        </ul>

        <h4 style="color: #38bdf8;">3. Połączenie Wi-Fi i PC Monitor (Port 1648):</h4>
        <ul>
            <li>W zakładce <i>Ustawienia</i> wgraj dane sieci Wi-Fi i IP komputera przez przycisk <b>Wgraj Wi-Fi i IP do ekranu (przez USB)</b>.</li>
            <li>Uruchom <b>Serwer TCP (Port 1648)</b>.</li>
            <li>Po przełączeniu na tryb <b>PC Monitor</b>, ekran natychmiast połączy się z aplikacją i zacznie wyświetlać zużycie procesora i pamięci RAM!</li>
        </ul>
        """

        tb.setHtml(html_content)
        dlg_layout.addWidget(tb)

        close_btn = QPushButton("Rozumiem, zamknij")
        close_btn.setObjectName("AccentButton")
        close_btn.clicked.connect(dlg.accept)
        dlg_layout.addWidget(close_btn, alignment=Qt.AlignCenter)

        dlg.exec()

    def on_config_updated(self):
        """Called whenever settings change."""
        pass

    def on_live_sync_toggled(self, checked: bool):
        if checked:
            self.sync_timer.start(2000)
            self.send_current_view_to_screen(silent=True)
        else:
            self.sync_timer.stop()

    def on_sync_tick(self):
        if not self.is_sending_frame:
            self.send_current_view_to_screen(silent=True)

    def send_current_view_to_screen(self, silent: bool = False):
        """Sends current rendered frame or switches active mode on physical LCD screen over Wi-Fi HTTP."""
        if self.is_sending_frame:
            return

        mode = self.config_mgr.get("current_mode", "custom")
        screen_ip = self.config_mgr.get("screen_ip", "192.168.1.115")
        self.http_ctrl.set_ip(screen_ip)

        # 1. Telemetry / PC Monitor mode
        if mode in ("usage", "temperatures"):
            def _worker_sysinfo():
                self.is_sending_frame = True
                pc_ip = self.config_mgr.get("pc_ip", "192.168.1.173")
                ok, msg = self.http_ctrl.switch_to_sysinfo(pc_ip=pc_ip, port=self.config_mgr.get("tcp_port", 1648))
                self.is_sending_frame = False
                if not self.net_server.running:
                    self.net_server.start()
                if not silent:
                    if ok:
                        self.push_to_screen_btn.setText("✅ Przełączono na PC Monitor")
                    else:
                        self.push_to_screen_btn.setText("⚠️ Błąd połączenia")
                    QTimer.singleShot(2500, lambda: self.push_to_screen_btn.setText("📡 Wyślij widok na ekran (Wi-Fi)"))
            threading.Thread(target=_worker_sysinfo, daemon=True).start()
            return

        # 2. Rendered Frame (Custom, Clock, Calendar, Image, Slideshow)
        current_frame = self.renderer.get_current_frame()
        if not current_frame:
            current_frame = self.renderer.render(self.config_mgr.config, self.current_metrics)

        # Clone image to avoid race condition
        frame_copy = current_frame.copy()

        def _worker_frame():
            self.is_sending_frame = True
            ok, msg = self.http_ctrl.upload_frame(frame_copy, filename="screen_live.jpg")
            self.is_sending_frame = False
            if not silent:
                if ok:
                    self.push_to_screen_btn.setText("✅ Wysłano na ekran LCD!")
                else:
                    self.push_to_screen_btn.setText("⚠️ Błąd wysyłania")
                QTimer.singleShot(2500, lambda: self.push_to_screen_btn.setText("📡 Wyślij widok na ekran (Wi-Fi)"))

        threading.Thread(target=_worker_frame, daemon=True).start()

    def on_metrics_tick(self):
        """Periodic hardware poll."""
        self.current_metrics = self.monitor.get_all_metrics()
        self.system_tab.update_live_metrics(self.current_metrics)

        # Update status bar
        cpu = self.current_metrics.get('cpu_percent', 0.0)
        ram = self.current_metrics.get('ram_percent', 0.0)
        gpu = self.current_metrics.get('gpu_percent', 0.0)
        cpu_t = self.current_metrics.get('cpu_temp', 0.0)
        gpu_t = self.current_metrics.get('gpu_temp', 0.0)
        nvme_t = self.current_metrics.get('nvme_temp', 0.0)

        self.sb_stats_lbl.setText(
            f"⚡ CPU: {cpu:.0f}% ({cpu_t:.0f}°C) | 💾 RAM: {ram:.0f}% | 🎮 GPU: {gpu:.0f}% ({gpu_t:.0f}°C) | 💿 NVMe: {nvme_t:.0f}°C"
        )

        if self.net_server.running:
            client_count = len(self.net_server.clients)
            self.sb_net_lbl.setText(f"🌐 TCP 1648 (Połączono: {client_count})")
            self.sb_net_lbl.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            self.sb_net_lbl.setText("🌐 TCP (Wyłączony)")
            self.sb_net_lbl.setStyleSheet("color: #ef4444; font-weight: bold;")

    def on_render_tick(self):
        """Renders LCD screen frame and updates preview widget."""
        frame = self.renderer.render(self.config_mgr.config, self.current_metrics)
        mode_name = self.config_mgr.get("current_mode", "Custom").capitalize()
        self.preview_widget.update_frame(frame, mode_name)

        # FPS calculation
        self.frame_count += 1
        now = time.time()
        if now - self.fps_last_time >= 1.0:
            fps = self.frame_count / (now - self.fps_last_time)
            self.preview_widget.fps_lbl.setText(f"{fps:.0f} FPS")
            self.frame_count = 0
            self.fps_last_time = now

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_and_activate()

    def show_and_activate(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        """Minimize to tray on close."""
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            self.close_application()

    def close_application(self):
        self.net_server.stop()
        self.serial_ctrl.disconnect()
        self.config_mgr.save()
        sys.exit(0)
