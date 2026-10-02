import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QGroupBox
)
from PySide6.QtCore import Signal
from lcd_core.config_manager import ConfigManager

class DualGaugesPanel(QWidget):
    settings_changed = Signal()

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self.config_mgr = config_mgr
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        box = QGroupBox("🏎️ Ustawienia Zegarów Wyścigowych (Dual Tachometer)")
        b_layout = QVBoxLayout(box)

        # Style
        s_row = QHBoxLayout()
        s_row.addWidget(QLabel("🏁 Styl obrotomierza:"))
        self.style_combo = QComboBox()
        self.style_combo.addItem("Sport Tachometer (CPU + GPU)", "sport_tachometer")
        self.style_combo.addItem("Turbo Boost Meter", "turbo_boost")
        self.style_combo.addItem("Classic Analog Clocks", "classic_analog")
        
        cur_s = self.config_mgr.get("gauges_style", "sport_tachometer")
        idx = self.style_combo.findData(cur_s)
        if idx >= 0:
            self.style_combo.setCurrentIndex(idx)
        self.style_combo.currentIndexChanged.connect(self.on_style_changed)
        s_row.addWidget(self.style_combo, 1)
        b_layout.addLayout(s_row)

        # Toggles
        self.show_temps_cb = QCheckBox("Wyświetlaj cyfrowe temperatury w środkowym bloku")
        self.show_temps_cb.setChecked(self.config_mgr.get("gauges_show_temps", True))
        self.show_temps_cb.toggled.connect(lambda v: self.update_cfg("gauges_show_temps", v))
        b_layout.addWidget(self.show_temps_cb)

        self.show_ram_cb = QCheckBox("Wyświetlaj dolny pasek pamięci RAM i NVMe")
        self.show_ram_cb.setChecked(self.config_mgr.get("gauges_show_ram", True))
        self.show_ram_cb.toggled.connect(lambda v: self.update_cfg("gauges_show_ram", v))
        b_layout.addWidget(self.show_ram_cb)

        layout.addWidget(box)
        layout.addStretch()

    def on_style_changed(self):
        val = self.style_combo.currentData()
        self.config_mgr.set("gauges_style", val)
        self.settings_changed.emit()

    def update_cfg(self, key: str, val: bool):
        self.config_mgr.set(key, val)
        self.settings_changed.emit()
