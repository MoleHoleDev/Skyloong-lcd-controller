import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QLineEdit, QComboBox, QGroupBox
)
from PySide6.QtCore import Signal
from lcd_core.config_manager import ConfigManager

class RetroSynthwavePanel(QWidget):
    settings_changed = Signal()

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self.config_mgr = config_mgr
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Title / Description
        title_box = QGroupBox("🌆 Ustawienia Retro Synthwave HUD")
        title_layout = QVBoxLayout(title_box)

        # Palette
        p_row = QHBoxLayout()
        p_row.addWidget(QLabel("🎨 Paleta kolorów:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Neon Sunset (Róż / Cyjan / Żółty)", "neon_sunset")
        self.theme_combo.addItem("Cyber Grid (Fiolet / Cyjan)", "cyber_grid")
        self.theme_combo.addItem("Outrun Purple (Ciemny Fiolet)", "outrun_purple")
        self.theme_combo.addItem("Laser Blue (Niebieski / Morski)", "laser_blue")
        
        cur_t = self.config_mgr.get("synthwave_theme", "neon_sunset")
        idx = self.theme_combo.findData(cur_t)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        p_row.addWidget(self.theme_combo, 1)
        title_layout.addLayout(p_row)

        # Custom text
        txt_row = QHBoxLayout()
        txt_row.addWidget(QLabel("📝 Własny napis:"))
        self.text_input = QLineEdit()
        self.text_input.setText(self.config_mgr.get("synthwave_custom_text", "CYBERPUNK 2077"))
        self.text_input.setPlaceholderText("np. CYBERPUNK 2077 / MY RIG")
        self.text_input.textChanged.connect(self.on_text_changed)
        txt_row.addWidget(self.text_input, 1)
        title_layout.addLayout(txt_row)

        # Toggles
        self.show_sun_cb = QCheckBox("Wyświetlaj retro słońce nad horyzontem")
        self.show_sun_cb.setChecked(self.config_mgr.get("synthwave_show_sun", True))
        self.show_sun_cb.toggled.connect(lambda v: self.update_cfg("synthwave_show_sun", v))
        title_layout.addWidget(self.show_sun_cb)

        self.show_clock_cb = QCheckBox("Wyświetlaj cyfrowy zegar w lewym rogu")
        self.show_clock_cb.setChecked(self.config_mgr.get("synthwave_show_clock", True))
        self.show_clock_cb.toggled.connect(lambda v: self.update_cfg("synthwave_show_clock", v))
        title_layout.addWidget(self.show_clock_cb)

        self.show_telemetry_cb = QCheckBox("Wyświetlaj karty telemetrii (CPU/GPU/RAM/Temp)")
        self.show_telemetry_cb.setChecked(self.config_mgr.get("synthwave_show_telemetry", True))
        self.show_telemetry_cb.toggled.connect(lambda v: self.update_cfg("synthwave_show_telemetry", v))
        title_layout.addWidget(self.show_telemetry_cb)

        layout.addWidget(title_box)
        layout.addStretch()

    def on_theme_changed(self):
        val = self.theme_combo.currentData()
        self.config_mgr.set("synthwave_theme", val)
        self.settings_changed.emit()

    def on_text_changed(self, text: str):
        self.config_mgr.set("synthwave_custom_text", text)
        self.settings_changed.emit()

    def update_cfg(self, key: str, val: bool):
        self.config_mgr.set(key, val)
        self.settings_changed.emit()
