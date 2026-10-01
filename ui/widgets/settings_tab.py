import os
import sys
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSpinBox, QGroupBox, QLineEdit, QMessageBox, QTextEdit, QScrollArea,
    QFrame, QApplication, QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCursor

from lcd_core.config_manager import ConfigManager
from lcd_core.network_server import NetworkServer
from lcd_core.serial_controller import SerialController
from lcd_core.usb_permissions import fix_usb_permissions, is_port_accessible
from lcd_core.esp_manager import ESPManager
from lcd_core.http_controller import HTTPController

class SettingsTab(QWidget):
    config_changed = Signal()

    def __init__(self, config_mgr: ConfigManager, net_server: NetworkServer, serial_ctrl: SerialController, http_ctrl: HTTPController = None, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.net_server = net_server
        self.serial_ctrl = serial_ctrl
        self.http_ctrl = http_ctrl or HTTPController(self.config_mgr.get("screen_ip", "192.168.1.115"))
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main Vertical-Only Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(14)

        # ----------------------------------------------------
        # 1. LCD Screen Wi-Fi Connection (HTTP API)
        # ----------------------------------------------------
        http_group = QGroupBox("📺 Połączenie z ekranem LCD przez Wi-Fi (HTTP API)")
        http_layout = QVBoxLayout(http_group)
        http_layout.setSpacing(8)

        http_info = QLabel(
            "Ekran jest podłączony do Twojej sieci Wi-Fi i posiada własny serwer HTTP. "
            "Możesz bezpośrednio wysyłać na niego wygenerowane obrazy i przełączać tryby bez dotykania klawiatury."
        )
        http_info.setWordWrap(True)
        http_info.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        http_layout.addWidget(http_info)

        ip_screen_row = QHBoxLayout()
        ip_screen_row.addWidget(QLabel("Adres IP ekranu LCD:"))
        self.screen_ip_input = QLineEdit()
        self.screen_ip_input.setText(self.config_mgr.get("screen_ip", "192.168.1.115"))
        self.screen_ip_input.setPlaceholderText("np. 192.168.1.115")
        self.screen_ip_input.textChanged.connect(self.on_screen_ip_changed)
        ip_screen_row.addWidget(self.screen_ip_input, 1)

        self.test_screen_btn = QPushButton("🔍 Sprawdź połączenie")
        self.test_screen_btn.clicked.connect(self.test_screen_connection)
        ip_screen_row.addWidget(self.test_screen_btn)
        http_layout.addLayout(ip_screen_row)

        self.screen_http_status_lbl = QLabel("⚪ Nie sprawdzono")
        self.screen_http_status_lbl.setStyleSheet(
            "font-weight: bold; color: #94a3b8; padding: 6px 10px; background: #090d16; border-radius: 4px; font-size: 11px; border: 1px solid #1e293b;"
        )
        http_layout.addWidget(self.screen_http_status_lbl)

        screen_actions_row = QHBoxLayout()
        self.switch_sysinfo_btn = QPushButton("📊 Monitor PC (CPU/RAM)")
        self.switch_sysinfo_btn.clicked.connect(self.http_switch_sysinfo)
        screen_actions_row.addWidget(self.switch_sysinfo_btn)

        self.switch_jpg_btn = QPushButton("🖼️ Tryb Zdjęć")
        self.switch_jpg_btn.clicked.connect(self.http_switch_jpg)
        screen_actions_row.addWidget(self.switch_jpg_btn)

        self.switch_gif_btn = QPushButton("🎞️ Tryb GIF/Wideo")
        self.switch_gif_btn.clicked.connect(self.http_switch_gif)
        screen_actions_row.addWidget(self.switch_gif_btn)
        http_layout.addLayout(screen_actions_row)

        # Theme Switcher
        theme_title = QLabel("🎨 Motyw wbudowanego zegara na ekranie:")
        theme_title.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 11px; margin-top: 4px;")
        http_layout.addWidget(theme_title)

        theme_row = QHBoxLayout()
        self.theme0_btn = QPushButton("⚡ Motyw 1 (Cyberpunk)")
        self.theme0_btn.clicked.connect(lambda: self.http_switch_theme(0))
        theme_row.addWidget(self.theme0_btn)

        self.theme1_btn = QPushButton("🕒 Motyw 2 (Cyfrowy)")
        self.theme1_btn.clicked.connect(lambda: self.http_switch_theme(1))
        theme_row.addWidget(self.theme1_btn)

        self.theme2_btn = QPushButton("📟 Motyw 3 (Retro LCD)")
        self.theme2_btn.clicked.connect(lambda: self.http_switch_theme(2))
        theme_row.addWidget(self.theme2_btn)
        http_layout.addLayout(theme_row)

        # Userdata / Custom Text & City
        user_row = QHBoxLayout()
        user_row.addWidget(QLabel("Własny tekst:"))
        self.userdata_input = QLineEdit()
        self.userdata_input.setText(self.config_mgr.get("screen_userdata", "Skyloong GK104"))
        self.userdata_input.setPlaceholderText("Własny napis pod zegarem")
        user_row.addWidget(self.userdata_input, 2)

        user_row.addWidget(QLabel("Miasto:"))
        self.city_input = QLineEdit()
        self.city_input.setText(self.config_mgr.get("screen_city", "Warszawa"))
        self.city_input.setPlaceholderText("Miasto")
        user_row.addWidget(self.city_input, 1)

        self.save_text_btn = QPushButton("💾 Zapisz tekst")
        self.save_text_btn.clicked.connect(self.save_screen_userdata)
        user_row.addWidget(self.save_text_btn)
        http_layout.addLayout(user_row)

        layout.addWidget(http_group)

        # ----------------------------------------------------
        # 2. TCP Server & PC IP Addresses Group
        # ----------------------------------------------------
        tcp_group = QGroupBox("🌐 Serwer PC & Adresy IP w sieci lokalnej (Port 1648)")
        tcp_layout = QVBoxLayout(tcp_group)
        tcp_layout.setSpacing(8)

        # IP List Description
        ip_desc = QLabel("Wybierz adres IP swojego komputera (widoczny dla ekranu w sieci lokalnej):")
        ip_desc.setWordWrap(True)
        ip_desc.setStyleSheet("color: #94a3b8; font-size: 11px;")
        tcp_layout.addWidget(ip_desc)

        # IP List Widget
        self.ip_list_widget = QListWidget()
        self.ip_list_widget.setStyleSheet("""
            QListWidget {
                background: #090d16;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 4px;
                font-family: monospace;
                font-size: 11px;
            }
            QListWidget::item {
                padding: 5px 8px;
                border-radius: 4px;
                color: #e2e8f0;
            }
            QListWidget::item:selected {
                background: #0284c7;
                color: #ffffff;
                font-weight: bold;
            }
        """)
        self.ip_list_widget.setFixedHeight(85)
        self.ip_list_widget.itemClicked.connect(self.on_ip_item_clicked)
        tcp_layout.addWidget(self.ip_list_widget)

        ip_btn_row = QHBoxLayout()
        refresh_ip_btn = QPushButton("🔄 Odśwież listę IP")
        refresh_ip_btn.clicked.connect(self.refresh_ip_list)
        ip_btn_row.addWidget(refresh_ip_btn)

        copy_ip_btn = QPushButton("📋 Kopiuj wybrany IP")
        copy_ip_btn.clicked.connect(self.copy_selected_ip)
        ip_btn_row.addWidget(copy_ip_btn)
        tcp_layout.addLayout(ip_btn_row)

        self.refresh_ip_list()

        # TCP Server Controls Row
        port_row = QHBoxLayout()
        port_row.addWidget(QLabel("Port TCP:"))
        self.port_spin = QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(self.config_mgr.get("tcp_port", 1648))
        self.port_spin.valueChanged.connect(lambda v: self.config_mgr.set("tcp_port", v))
        port_row.addWidget(self.port_spin)

        self.tcp_status_lbl = QLabel("🔴 Nieaktywny")
        self.tcp_status_lbl.setStyleSheet("font-weight: bold; color: #ef4444; padding: 3px 8px; background: #0f172a; border-radius: 4px; font-size: 11px;")
        port_row.addWidget(self.tcp_status_lbl)
        tcp_layout.addLayout(port_row)

        tcp_btn_row = QHBoxLayout()
        self.start_tcp_btn = QPushButton("▶ Uruchom serwer TCP")
        self.start_tcp_btn.setObjectName("AccentButton")
        self.start_tcp_btn.clicked.connect(self.toggle_tcp_server)
        tcp_btn_row.addWidget(self.start_tcp_btn, 1)

        self.tcp_clients_lbl = QLabel("Połączonych ekranów: 0")
        self.tcp_clients_lbl.setStyleSheet("color: #94a3b8; font-weight: 500; font-size: 11px;")
        tcp_btn_row.addWidget(self.tcp_clients_lbl)
        tcp_layout.addLayout(tcp_btn_row)

        layout.addWidget(tcp_group)

        # ----------------------------------------------------
        # 2. Wi-Fi & IP Direct Upload via USB (LittleFS)
        # ----------------------------------------------------
        wifi_group = QGroupBox("📶 Wgrywanie ustawień Wi-Fi i IP do ekranu (przez USB)")
        wifi_layout = QVBoxLayout(wifi_group)
        wifi_layout.setSpacing(8)

        wifi_info = QLabel(
            "Wgraj dane sieci Wi-Fi i adres IP komputera bezpośrednio do pamięci wewnętrznej ekranu przez USB. "
            "Ekran natychmiast połączy się z Twoją siecią bez konieczności skanowania kodu QR czy łączenia z hotspotem."
        )
        wifi_info.setWordWrap(True)
        wifi_info.setStyleSheet("color: #cbd5e1; font-size: 11px;")
        wifi_layout.addWidget(wifi_info)

        # SSID Field with Auto-Detect Button
        ssid_row = QHBoxLayout()
        ssid_row.addWidget(QLabel("Nazwa sieci (SSID):"))
        self.wifi_ssid_input = QLineEdit()
        self.wifi_ssid_input.setPlaceholderText("Wpisz SSID lub kliknij Pobierz z systemu...")
        ssid_row.addWidget(self.wifi_ssid_input, 1)

        detect_wifi_btn = QPushButton("🔄 Pobierz z systemu")
        detect_wifi_btn.setToolTip("Automatycznie pobiera nazwę i hasło aktywnego połączenia Wi-Fi z systemu Linux (NetworkManager).")
        detect_wifi_btn.clicked.connect(self.auto_detect_wifi)
        ssid_row.addWidget(detect_wifi_btn)
        wifi_layout.addLayout(ssid_row)

        # Password Field with Show/Hide checkbox
        pw_row = QHBoxLayout()
        pw_row.addWidget(QLabel("Hasło Wi-Fi:"))
        self.wifi_pw_input = QLineEdit()
        self.wifi_pw_input.setEchoMode(QLineEdit.Password)
        self.wifi_pw_input.setPlaceholderText("Wpisz hasło do sieci Wi-Fi...")
        pw_row.addWidget(self.wifi_pw_input, 1)

        self.show_pw_cb = QCheckBox("Pokaż")
        self.show_pw_cb.toggled.connect(lambda checked: self.wifi_pw_input.setEchoMode(QLineEdit.Normal if checked else QLineEdit.Password))
        pw_row.addWidget(self.show_pw_cb)
        wifi_layout.addLayout(pw_row)

        # Target PC IP Field
        target_ip_row = QHBoxLayout()
        target_ip_row.addWidget(QLabel("Adres IP PC:"))
        self.target_ip_input = QLineEdit()
        self.target_ip_input.setPlaceholderText("np. 192.168.1.173")
        # Pre-fill with first detected IP
        ips = ESPManager.get_pc_network_ips()
        if ips:
            self.target_ip_input.setText(ips[0]["ip"])
        target_ip_row.addWidget(self.target_ip_input, 1)

        # Nickname field
        target_ip_row.addWidget(QLabel("Nazwa:"))
        self.nickname_input = QLineEdit("PC")
        self.nickname_input.setMaximumWidth(80)
        target_ip_row.addWidget(self.nickname_input)
        wifi_layout.addLayout(target_ip_row)

        # Big Flash / Upload Button
        self.flash_wifi_btn = QPushButton("🚀 Wgraj Wi-Fi i IP do ekranu (przez USB)")
        self.flash_wifi_btn.setObjectName("AccentButton")
        self.flash_wifi_btn.setStyleSheet("font-weight: bold; font-size: 12px; padding: 8px;")
        self.flash_wifi_btn.clicked.connect(self.on_flash_wifi_clicked)
        wifi_layout.addWidget(self.flash_wifi_btn)

        # Wi-Fi Reset & Reboot Row
        esp_sub_row = QHBoxLayout()
        self.reset_wifi_btn = QPushButton("🧹 Wyczyść pamięć Wi-Fi")
        self.reset_wifi_btn.setObjectName("DangerButton")
        self.reset_wifi_btn.setToolTip("Usuwa zapisane dane Wi-Fi w pamięci flash ekranu.")
        self.reset_wifi_btn.clicked.connect(self.on_reset_wifi_clicked)
        esp_sub_row.addWidget(self.reset_wifi_btn)

        self.reboot_esp_btn = QPushButton("⚡ Zrestartuj ekran")
        self.reboot_esp_btn.clicked.connect(self.on_reboot_esp_clicked)
        esp_sub_row.addWidget(self.reboot_esp_btn)
        wifi_layout.addLayout(esp_sub_row)

        layout.addWidget(wifi_group)

        # ----------------------------------------------------
        # 3. USB Serial & Permissions Group
        # ----------------------------------------------------
        serial_group = QGroupBox("🔌 Połączenie szeregowe USB & Diagnostyka")
        serial_layout = QVBoxLayout(serial_group)
        serial_layout.setSpacing(8)

        serial_row = QHBoxLayout()
        serial_row.addWidget(QLabel("Port USB:"))
        self.port_combo = QComboBox()
        self.refresh_serial_ports()
        serial_row.addWidget(self.port_combo, 1)

        refresh_ports_btn = QPushButton("🔄")
        refresh_ports_btn.setToolTip("Odśwież listę portów USB")
        refresh_ports_btn.clicked.connect(self.refresh_serial_ports)
        serial_row.addWidget(refresh_ports_btn)

        self.serial_status_lbl = QLabel("🔴 Rozłączono")
        self.serial_status_lbl.setStyleSheet("font-weight: bold; color: #ef4444; padding: 3px 8px; background: #0f172a; border-radius: 4px; font-size: 11px;")
        serial_row.addWidget(self.serial_status_lbl)
        serial_layout.addLayout(serial_row)

        serial_btn_row = QHBoxLayout()
        self.connect_serial_btn = QPushButton("🔌 Połącz USB")
        self.connect_serial_btn.clicked.connect(self.toggle_serial)
        serial_btn_row.addWidget(self.connect_serial_btn)

        self.fix_perm_btn = QPushButton("🛡️ Odblokuj uprawnienia USB (GUI)")
        self.fix_perm_btn.setToolTip("Automatycznie nadaje uprawnienia do portu USB za pomocą systemowego okna autoryzacji (bez terminala).")
        self.fix_perm_btn.clicked.connect(self.on_fix_permissions_clicked)
        serial_btn_row.addWidget(self.fix_perm_btn)
        serial_layout.addLayout(serial_btn_row)

        # Hardware Control via USB (debug_USB_UART commands)
        usb_ctrl_label = QLabel("🎮 Sterowanie ekranem przez kabel USB (debug UART):")
        usb_ctrl_label.setStyleSheet("font-weight: bold; color: #38bdf8; font-size: 11px; margin-top: 4px;")
        serial_layout.addWidget(usb_ctrl_label)

        usb_actions_row = QHBoxLayout()
        self.usb_switch_app_btn = QPushButton("⚡ Następna aplikacja (USB `)")
        self.usb_switch_app_btn.setObjectName("AccentButton")
        self.usb_switch_app_btn.setToolTip("Wysyła znak '`' (backtick) przez USB, co natychmiast przełącza ekran na kolejną aplikację (Zegar -> APS -> GIF -> Pogoda -> Sysinfo PC Monitor).")
        self.usb_switch_app_btn.clicked.connect(self.on_usb_switch_app_clicked)
        usb_actions_row.addWidget(self.usb_switch_app_btn, 2)

        self.usb_toggle_menu_btn = QPushButton("⚙️ Menu LCD (USB /)")
        self.usb_toggle_menu_btn.setToolTip("Wysyła znak '/' przez USB, co wchodzi lub wychodzi z wbudowanego menu ustawień na ekranie.")
        self.usb_toggle_menu_btn.clicked.connect(self.on_usb_toggle_menu_clicked)
        usb_actions_row.addWidget(self.usb_toggle_menu_btn, 1)
        serial_layout.addLayout(usb_actions_row)

        # On-Screen D-Pad Navigation Buttons
        dpad_row = QHBoxLayout()
        dpad_row.addWidget(QLabel("Nawigacja menu:"))

        btn_up = QPushButton("⬆ W")
        btn_up.setToolTip("Wysyła 'w' (Góra / Poprzednia pozycja)")
        btn_up.clicked.connect(lambda: self.on_usb_nav_clicked("w"))
        dpad_row.addWidget(btn_up)

        btn_down = QPushButton("⬇ S")
        btn_down.setToolTip("Wysyła 's' (Dół / Następna pozycja)")
        btn_down.clicked.connect(lambda: self.on_usb_nav_clicked("s"))
        dpad_row.addWidget(btn_down)

        btn_left = QPushButton("⬅ A")
        btn_left.setToolTip("Wysyła 'a' (W lewo)")
        btn_left.clicked.connect(lambda: self.on_usb_nav_clicked("a"))
        dpad_row.addWidget(btn_left)

        btn_right = QPushButton("➡ D")
        btn_right.setToolTip("Wysyła 'd' (W prawo)")
        btn_right.clicked.connect(lambda: self.on_usb_nav_clicked("d"))
        dpad_row.addWidget(btn_right)

        btn_enter = QPushButton("⏎ Enter")
        btn_enter.setToolTip("Wysyła '\\n' (Enter / Zatwierdź)")
        btn_enter.clicked.connect(lambda: self.on_usb_nav_clicked("\n"))
        dpad_row.addWidget(btn_enter)
        serial_layout.addLayout(dpad_row)

        # Serial Live Log Console
        self.log_console = QTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setStyleSheet("background: #020617; color: #a5f3fc; font-family: monospace; font-size: 11px; border-radius: 4px; padding: 4px;")
        self.log_console.setMaximumHeight(110)
        serial_layout.addWidget(self.log_console)

        log_cmd_row = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Polecenie do wysłania po USB...")
        self.cmd_input.returnPressed.connect(self.send_custom_serial_cmd)
        log_cmd_row.addWidget(self.cmd_input, 1)

        send_cmd_btn = QPushButton("Wyślij")
        send_cmd_btn.clicked.connect(self.send_custom_serial_cmd)
        log_cmd_row.addWidget(send_cmd_btn)

        clear_log_btn = QPushButton("Wyczyść")
        clear_log_btn.clicked.connect(self.log_console.clear)
        log_cmd_row.addWidget(clear_log_btn)
        serial_layout.addLayout(log_cmd_row)

        layout.addWidget(serial_group)

        # ----------------------------------------------------
        # 4. Display Settings & Defaults
        # ----------------------------------------------------
        bottom_row = QHBoxLayout()
        
        self.res_combo = QComboBox()
        res_items = [
            ("240 x 240 px (Skyloong GK104 Pro)", "240x240"),
            ("320 x 240 px (Panoramiczny 4:3)", "320x240")
        ]
        for text, data in res_items:
            self.res_combo.addItem(text, data)
        self.res_combo.currentIndexChanged.connect(self.on_res_changed)
        bottom_row.addWidget(QLabel("Rozdzielczość:"))
        bottom_row.addWidget(self.res_combo, 1)

        reset_def_btn = QPushButton("↺ Reset programu")
        reset_def_btn.setObjectName("DangerButton")
        reset_def_btn.clicked.connect(self.reset_defaults)
        bottom_row.addWidget(reset_def_btn)
        layout.addLayout(bottom_row)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Connect internal callbacks / signals
        self.net_server.on_status_change = self.on_net_status
        self.net_server.on_clients_change = self.on_net_clients
        self.serial_ctrl.sig_status_change.connect(self.on_serial_status)
        self.serial_ctrl.sig_log.connect(self.append_log)
        self.serial_ctrl.sig_data_received.connect(self.append_serial_data)

        # Auto-detect wifi initially
        self.auto_detect_wifi(silent=True)

    def refresh_ip_list(self):
        self.ip_list_widget.clear()
        ips = ESPManager.get_pc_network_ips()
        if not ips:
            item = QListWidgetItem("Brak wykrytych adresów IP")
            self.ip_list_widget.addItem(item)
            return

        for item_data in ips:
            iface = item_data["iface"]
            ip = item_data["ip"]
            if_type = item_data.get("type", "Inne")
            icon = "📶" if if_type == "Wi-Fi" else ("🌐" if if_type == "Ethernet" else "🔗")
            list_item = QListWidgetItem(f"{icon} {iface} [{if_type}]:  {ip}")
            list_item.setData(Qt.UserRole, ip)
            self.ip_list_widget.addItem(list_item)

        if self.ip_list_widget.count() > 0:
            self.ip_list_widget.setCurrentRow(0)

    def on_ip_item_clicked(self, item: QListWidgetItem):
        ip = item.data(Qt.UserRole)
        if ip:
            self.target_ip_input.setText(ip)

    def copy_selected_ip(self):
        item = self.ip_list_widget.currentItem()
        if item:
            ip = item.data(Qt.UserRole)
            if ip:
                clipboard = QApplication.clipboard()
                clipboard.setText(ip)
                self.append_log(f"Skopiowano adres IP do schowka: {ip}")
                QMessageBox.information(self, "Skopiowano", f"Skopiowano adres IP do schowka:\n{ip}")

    def auto_detect_wifi(self, silent: bool = False):
        ssid, password = ESPManager.get_active_system_wifi()
        if ssid:
            self.wifi_ssid_input.setText(ssid)
            if password:
                self.wifi_pw_input.setText(password)
            self.append_log(f"Wykryto aktywną sieć Wi-Fi: {ssid}")
            if not silent:
                QMessageBox.information(self, "Wykryto sieć Wi-Fi", f"Pobrano aktywną sieć Wi-Fi z systemu:\nSSID: {ssid}")
        elif not silent:
            QMessageBox.warning(self, "Brak sieci Wi-Fi", "Nie udało się automatycznie wykryć aktywnego połączenia Wi-Fi.")

    def on_flash_wifi_clicked(self):
        port = self.port_combo.currentText()
        ssid = self.wifi_ssid_input.text().strip()
        pw = self.wifi_pw_input.text().strip()
        pc_ip = self.target_ip_input.text().strip()
        nick = self.nickname_input.text().strip() or "PC"

        if not port:
            QMessageBox.warning(self, "Brak portu USB", "Wybierz port USB ekranika.")
            return

        if not ssid:
            QMessageBox.warning(self, "Brak SSID", "Wprowadź nazwę sieci Wi-Fi (SSID).")
            return

        if not pc_ip:
            QMessageBox.warning(self, "Brak adresu IP", "Wprowadź adres IP Twojego komputera.")
            return

        reply = QMessageBox.question(
            self, "Potwierdzenie zapisu",
            f"Czy chcesz wgrać konfigurację do ekranu przez USB ({port})?\n\n"
            f"• Sieć Wi-Fi: {ssid}\n"
            f"• Adres IP komputera: {pc_ip}\n"
            f"• Nazwa profilu: {nick}\n\n"
            "Moduł ESP32 zostanie zaktualizowany i automatycznie zrestartowany.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        was_connected = self.serial_ctrl.connected
        if was_connected:
            self.serial_ctrl.disconnect()

        self.append_log(f"Wgrywanie Wi-Fi ({ssid}) i IP ({pc_ip}) do pamięci flash ekranu...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        ok, msg = ESPManager.write_wifi_and_ip_to_esp32(
            port=port, ssid=ssid, password=pw, pc_ip=pc_ip, nickname=nick
        )
        QApplication.restoreOverrideCursor()

        if ok:
            QMessageBox.information(self, "Sukces wgrywania", msg)
            self.append_log(f"Sukces: {msg}")
        else:
            QMessageBox.critical(self, "Błąd wgrywania", msg)
            self.append_log(f"Błąd wgrywania: {msg}")

        if was_connected:
            self.serial_ctrl.connect(port=port)

    def refresh_serial_ports(self):
        self.port_combo.clear()
        ports = self.serial_ctrl.list_ports()
        if not ports:
            self.port_combo.addItem("/dev/ttyACM0")
            self.port_combo.addItem("/dev/ttyACM1")
        else:
            for p in ports:
                self.port_combo.addItem(p)

    def append_log(self, msg: str):
        self.log_console.append(f"<b>[App]</b> {msg}")
        self.log_console.moveCursor(QTextCursor.End)

    def append_serial_data(self, data: str):
        self.log_console.append(f"<span style='color: #4ade80;'>[ESP32]</span> {data}")
        self.log_console.moveCursor(QTextCursor.End)

    def send_custom_serial_cmd(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        if not self.serial_ctrl.connected:
            QMessageBox.warning(self, "Brak połączenia", "Najpierw połącz się z portem USB.")
            return
        self.serial_ctrl.send_data((cmd + "\n").encode("utf-8"))
        self.append_log(f"Wysłano: {cmd}")
        self.cmd_input.clear()

    def on_usb_switch_app_clicked(self):
        port = self.port_combo.currentText()
        ok, msg = self.serial_ctrl.switch_app(port=port)
        if ok:
            self.append_log(f"<b>[USB]</b> Przełączono aplikację na ekranie (sygnał `).")
        else:
            self.append_log(f"<b>[USB Błąd]</b> {msg}")
            QMessageBox.warning(self, "Błąd przełączania USB", msg)

    def on_usb_toggle_menu_clicked(self):
        port = self.port_combo.currentText()
        ok, msg = self.serial_ctrl.toggle_settings_menu(port=port)
        if ok:
            self.append_log(f"<b>[USB]</b> Wysłano sygnał menu ustawień (/)...")
        else:
            self.append_log(f"<b>[USB Błąd]</b> {msg}")
            QMessageBox.warning(self, "Błąd menu USB", msg)

    def on_usb_nav_clicked(self, key: str):
        port = self.port_combo.currentText()
        ok, msg = self.serial_ctrl.send_command(key.encode("utf-8"), port=port)
        if not ok:
            self.append_log(f"<b>[USB Błąd]</b> {msg}")

    def on_fix_permissions_clicked(self):
        port = self.port_combo.currentText()
        ok, msg = fix_usb_permissions(port)
        if ok:
            QMessageBox.information(self, "Uprawnienia USB", msg)
            self.append_log(msg)
        else:
            QMessageBox.warning(self, "Błąd autoryzacji", msg)
            self.append_log(f"Błąd: {msg}")

    def on_reset_wifi_clicked(self):
        port = self.port_combo.currentText()
        reply = QMessageBox.question(
            self, "Reset Wi-Fi w ekranie",
            f"Czy na pewno chcesz usunąć zapisaną konfigurację Wi-Fi w pamięci ekranu ({port})?\n\n"
            "Spowoduje to wyczyszczenie starych danych sieciowych.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        was_connected = self.serial_ctrl.connected
        if was_connected:
            self.serial_ctrl.disconnect()

        self.append_log(f"Rozpoczynanie czyszczenia danych Wi-Fi w pamięci flash ({port})...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        ok, msg = ESPManager.reset_esp32_nvs_wifi(port)
        QApplication.restoreOverrideCursor()

        if ok:
            QMessageBox.information(self, "Sukces resetu Wi-Fi", msg)
            self.append_log(msg)
        else:
            QMessageBox.critical(self, "Błąd resetowania Wi-Fi", msg)
            self.append_log(f"Błąd resetu Wi-Fi: {msg}")

        if was_connected:
            self.serial_ctrl.connect(port=port)

    def on_reboot_esp_clicked(self):
        port = self.port_combo.currentText()
        was_connected = self.serial_ctrl.connected
        if was_connected:
            self.serial_ctrl.disconnect()

        self.append_log(f"Wysyłanie sygnału restartu do modułu ESP32 ({port})...")
        ok, msg = ESPManager.reboot_esp32(port)
        if ok:
            QMessageBox.information(self, "Restart ESP32", msg)
            self.append_log(msg)
        else:
            QMessageBox.warning(self, "Błąd restartu", msg)
            self.append_log(msg)

    def toggle_tcp_server(self):
        if self.net_server.running:
            self.net_server.stop()
        else:
            port = self.port_spin.value()
            proc_info = NetworkServer.get_process_using_port(port)
            if proc_info:
                pid, name = proc_info
                reply = QMessageBox.question(
                    self, "Port jest zajęty",
                    f"Port {port} jest aktualnie zajęty przez proces:\n"
                    f"• Nazwa: <b>{name}</b>\n"
                    f"• PID: <b>{pid}</b>\n\n"
                    "Czy chcesz automatycznie zamknąć ten proces i zwolnić port?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    NetworkServer.kill_process_on_port(port)
                    import time
                    time.sleep(0.5)

            success = self.net_server.start(port=port)
            if not success:
                proc_info = NetworkServer.get_process_using_port(port)
                err_detail = f"Port jest zajęty przez proces {proc_info[1]} (PID: {proc_info[0]})." if proc_info else "Upewnij się, że żadna inna usługa nie blokuje tego portu."
                QMessageBox.warning(
                    self, "Błąd serwera TCP",
                    f"Nie udało się uruchomić serwera na porcie {port}.\n\n{err_detail}"
                )

    def on_net_status(self, is_running: bool):
        if is_running:
            self.tcp_status_lbl.setText("🟢 Aktywny")
            self.tcp_status_lbl.setStyleSheet("font-weight: bold; color: #10b981; padding: 4px 8px; background: #0f172a; border-radius: 4px;")
            self.start_tcp_btn.setText("⏹ Zatrzymaj serwer TCP")
            self.start_tcp_btn.setObjectName("DangerButton")
        else:
            self.tcp_status_lbl.setText("🔴 Nieaktywny")
            self.tcp_status_lbl.setStyleSheet("font-weight: bold; color: #ef4444; padding: 4px 8px; background: #0f172a; border-radius: 4px;")
            self.start_tcp_btn.setText("▶ Uruchom serwer TCP")
            self.start_tcp_btn.setObjectName("AccentButton")

    def on_net_clients(self, count: int):
        self.tcp_clients_lbl.setText(f"Połączonych ekranów: {count}")

    def toggle_serial(self):
        if self.serial_ctrl.connected:
            self.serial_ctrl.disconnect()
        else:
            port = self.port_combo.currentText()
            if not port:
                QMessageBox.warning(self, "Brak portu", "Wybierz port szeregowy z listy.")
                return
            success = self.serial_ctrl.connect(port=port)
            if not success:
                err_msg = self.serial_ctrl.last_error or "Nie udało się połączyć z portem."
                QMessageBox.critical(
                    self, "Błąd połączenia USB",
                    f"Nie można nawiązać połączenia z {port}:\n\n{err_msg}"
                )

    def on_serial_status(self, connected: bool):
        if connected:
            self.serial_status_lbl.setText("🟢 Połączono")
            self.serial_status_lbl.setStyleSheet("font-weight: bold; color: #10b981; padding: 4px 8px; background: #0f172a; border-radius: 4px;")
            self.connect_serial_btn.setText("Rozłącz USB")
        else:
            self.serial_status_lbl.setText("🔴 Rozłączono")
            self.serial_status_lbl.setStyleSheet("font-weight: bold; color: #ef4444; padding: 4px 8px; background: #0f172a; border-radius: 4px;")
            self.connect_serial_btn.setText("🔌 Połącz USB")

    def on_screen_ip_changed(self, text: str):
        ip = text.strip()
        self.config_mgr.set("screen_ip", ip)
        self.http_ctrl.set_ip(ip)

    def test_screen_connection(self):
        ip = self.screen_ip_input.text().strip()
        self.http_ctrl.set_ip(ip)
        self.screen_http_status_lbl.setText("⏳ Sprawdzanie połączenia...")
        self.screen_http_status_lbl.setStyleSheet("color: #38bdf8; font-weight: bold; padding: 6px 10px; background: #090d16; border-radius: 4px; font-size: 11px; border: 1px solid #1e293b;")
        QApplication.processEvents()

        ok, data, msg = self.http_ctrl.get_info()
        if ok and data:
            ssid = data.get("ssid", "Nieznana")
            mode = data.get("mode", "STA")
            theme = data.get("theme", 0)
            self.screen_http_status_lbl.setText(f"🟢 Połączono z ekranem LCD!\n• IP: {ip} | SSID: {ssid} | Tryb: {mode} | Motyw: {theme}")
            self.screen_http_status_lbl.setStyleSheet("color: #10b981; font-weight: bold; padding: 6px 10px; background: #090d16; border-radius: 4px; font-size: 11px; border: 1px solid #059669;")
            QMessageBox.information(
                self, "Połączenie z ekranem LCD",
                f"Pomyślnie nawiązano łączność z ekranem pod adresem <b>{ip}</b>!<br><br>"
                f"• Sieć Wi-Fi: <b>{ssid}</b><br>"
                f"• Tryb pracy: <b>{mode}</b><br>"
                f"• Aktywny plik: <b>{data.get('jpg_file', 'brak')}</b>"
            )
        else:
            self.screen_http_status_lbl.setText(f"🔴 Błąd połączenia: {msg}")
            self.screen_http_status_lbl.setStyleSheet("color: #ef4444; font-weight: bold; padding: 6px 10px; background: #090d16; border-radius: 4px; font-size: 11px; border: 1px solid #b91c1c;")
            QMessageBox.warning(
                self, "Błąd połączenia z ekranem",
                f"Nie udało się połączyć z ekranem LCD pod adresem <b>{ip}</b>.<br><br>{msg}"
            )

    def http_switch_sysinfo(self):
        selected_ip = self.target_ip_input.text().strip() or "192.168.1.173"
        port = self.port_spin.value()
        
        # Ensure TCP server is running first
        if not self.net_server.running:
            self.net_server.start(port=port)

        # Update remote IP on ESP32 and enable Sysinfo
        ok, msg = self.http_ctrl.switch_to_sysinfo(pc_ip=selected_ip, port=port)
        if ok:
            QMessageBox.information(
                self, "Tryb PC Monitor",
                f"Ekran został przełączony w tryb monitorowania PC!<br><br>"
                f"• Skonfigurowany adres serwera: <b>{selected_ip}:{port}</b><br>"
                f"• Serwer TCP: <b>🟢 Aktywny</b><br><br>"
                "<i>Uwaga: Moduł ESP32 nawiązuje połączenie TCP w ciągu 5 sekund po przełączeniu.</i>"
            )
        else:
            QMessageBox.warning(self, "Błąd przełączania", msg)

    def http_switch_jpg(self):
        ok, msg = self.http_ctrl.switch_to_jpg(filename="test_lcd.jpg")
        if ok:
            QMessageBox.information(self, "Tryb Zdjęć", "Ekran został przełączony w tryb wyświetlania zdjęć.")
        else:
            QMessageBox.warning(self, "Błąd przełączania", msg)

    def http_switch_gif(self):
        ok, msg = self.http_ctrl.switch_to_gif()
        if ok:
            QMessageBox.information(self, "Tryb GIF", "Ekran został przełączony w tryb odtwarzania GIF / Wideo.")
        else:
            QMessageBox.warning(self, "Błąd przełączania", msg)

    def http_switch_theme(self, theme_idx: int):
        ok, msg = self.http_ctrl.switch_theme(theme_idx)
        if ok:
            QMessageBox.information(self, "Zmiana motywu zegara", f"Pomyślnie zmieniono motyw zegara na <b>Motyw {theme_idx + 1}</b>!")
        else:
            QMessageBox.warning(self, "Błąd zmiany motywu", msg)

    def save_screen_userdata(self):
        userdata = self.userdata_input.text().strip()
        city = self.city_input.text().strip()
        self.config_mgr.set("screen_userdata", userdata)
        self.config_mgr.set("screen_city", city)

        # Get current PC IP to maintain connection
        selected_ip = "192.168.1.173"
        if self.ip_list_widget.currentItem():
            text = self.ip_list_widget.currentItem().text()
            import re
            m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", text)
            if m:
                selected_ip = m.group(1)

        ok, msg = self.http_ctrl.set_config_json(
            pc_ip=selected_ip,
            port=self.port_spin.value(),
            city=city,
            userdata=userdata
        )
        if ok:
            QMessageBox.information(self, "Zapis konfiguracji ekranu", f"Zapisano tekst: <b>{userdata}</b> oraz miasto: <b>{city}</b> na ekranie LCD!")
        else:
            QMessageBox.warning(self, "Błąd zapisu", msg)

    def on_res_changed(self, idx: int):
        if idx == 0:
            self.config_mgr.set("width", 240)
            self.config_mgr.set("height", 240)
        else:
            self.config_mgr.set("width", 320)
            self.config_mgr.set("height", 240)
        self.config_changed.emit()

    def reset_defaults(self):
        reply = QMessageBox.question(
            self, "Reset ustawień", "Czy na pewno chcesz przywrócić wszystkie ustawienia domyślne?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            from lcd_core.config_manager import DEFAULT_CONFIG
            self.config_mgr.config = dict(DEFAULT_CONFIG)
            self.config_mgr.save()
            self.config_changed.emit()
            QMessageBox.information(self, "Sukces", "Przywrócono ustawienia fabryczne.")
