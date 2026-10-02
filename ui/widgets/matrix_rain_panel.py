import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QGroupBox, QSlider
)
from PySide6.QtCore import Qt, Signal
from lcd_core.config_manager import ConfigManager

class MatrixRainPanel(QWidget):
    settings_changed = Signal()

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self.config_mgr = config_mgr
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        box = QGroupBox("🟢 Ustawienia Matrix Digital Rain")
        b_layout = QVBoxLayout(box)

        # Color Theme
        c_row = QHBoxLayout()
        c_row.addWidget(QLabel("🎨 Kolorystyka Matrix:"))
        self.color_combo = QComboBox()
        self.color_combo.addItem("Classic Green (Zielony Fosfor)", "matrix_green")
        self.color_combo.addItem("Amber CRT (Bursztynowy Monitor)", "amber_crt")
        self.color_combo.addItem("Cyber Cyan (Neonowy Błękit)", "cyber_cyan")
        self.color_combo.addItem("Red Alert (Czerwony Alarm)", "red_alert")
        
        cur_c = self.config_mgr.get("matrix_color", "matrix_green")
        idx = self.color_combo.findData(cur_c)
        if idx >= 0:
            self.color_combo.setCurrentIndex(idx)
        self.color_combo.currentIndexChanged.connect(self.on_color_changed)
        c_row.addWidget(self.color_combo, 1)
        b_layout.addLayout(c_row)

        # Speed Slider
        s_row = QHBoxLayout()
        s_row.addWidget(QLabel("⚡ Prędkość deszczu kodu:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(5, 30)
        cur_s = int(self.config_mgr.get("matrix_speed", 1.0) * 10)
        self.speed_slider.setValue(cur_s)
        self.speed_lbl = QLabel(f"{cur_s / 10.0:.1f}x")
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        s_row.addWidget(self.speed_slider, 1)
        s_row.addWidget(self.speed_lbl)
        b_layout.addLayout(s_row)

        # Toggles
        self.show_clock_cb = QCheckBox("Wyświetlaj duży cyfrowy zegar w konsoli")
        self.show_clock_cb.setChecked(self.config_mgr.get("matrix_show_clock", True))
        self.show_clock_cb.toggled.connect(lambda v: self.update_cfg("matrix_show_clock", v))
        b_layout.addWidget(self.show_clock_cb)

        self.show_stats_cb = QCheckBox("Wyświetlaj macierz telemetrii (CPU, RAM, GPU, Temp)")
        self.show_stats_cb.setChecked(self.config_mgr.get("matrix_show_stats", True))
        self.show_stats_cb.toggled.connect(lambda v: self.update_cfg("matrix_show_stats", v))
        b_layout.addWidget(self.show_stats_cb)

        layout.addWidget(box)
        layout.addStretch()

    def on_color_changed(self):
        val = self.color_combo.currentData()
        self.config_mgr.set("matrix_color", val)
        self.settings_changed.emit()

    def on_speed_changed(self, val: int):
        speed = val / 10.0
        self.speed_lbl.setText(f"{speed:.1f}x")
        self.config_mgr.set("matrix_speed", speed)
        self.settings_changed.emit()

    def update_cfg(self, key: str, val: bool):
        self.config_mgr.set(key, val)
        self.settings_changed.emit()
