import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QComboBox, QGroupBox, QSlider
)
from PySide6.QtCore import Qt, Signal
from lcd_core.config_manager import ConfigManager

class AudioVisualizerPanel(QWidget):
    settings_changed = Signal()

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self.config_mgr = config_mgr
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        box = QGroupBox("🎵 Ustawienia Audio Spectrum & VU Meter")
        b_layout = QVBoxLayout(box)

        # Style
        s_row = QHBoxLayout()
        s_row.addWidget(QLabel("🎛️ Typ wizualizera:"))
        self.style_combo = QComboBox()
        self.style_combo.addItem("18-Pasmowy Spektrogram + Stereo VU", "spectrum_bars")
        self.style_combo.addItem("Podwójny Wskaźnik VU L/R (dB)", "dual_vu_meter")
        self.style_combo.addItem("Dynamiczna Fala Audio (Waveform)", "waveform_pulse")
        
        cur_s = self.config_mgr.get("audio_style", "spectrum_bars")
        idx = self.style_combo.findData(cur_s)
        if idx >= 0:
            self.style_combo.setCurrentIndex(idx)
        self.style_combo.currentIndexChanged.connect(self.on_style_changed)
        s_row.addWidget(self.style_combo, 1)
        b_layout.addLayout(s_row)

        # Sensitivity
        sens_row = QHBoxLayout()
        sens_row.addWidget(QLabel("🔊 Czułość sygnału:"))
        self.sens_slider = QSlider(Qt.Horizontal)
        self.sens_slider.setRange(5, 25)
        cur_sens = int(self.config_mgr.get("audio_sensitivity", 1.0) * 10)
        self.sens_slider.setValue(cur_sens)
        self.sens_lbl = QLabel(f"{cur_sens / 10.0:.1f}x")
        self.sens_slider.valueChanged.connect(self.on_sens_changed)
        sens_row.addWidget(self.sens_slider, 1)
        sens_row.addWidget(self.sens_lbl)
        b_layout.addLayout(sens_row)

        # Toggles
        self.show_peaks_cb = QCheckBox("Wyświetlaj markery wartości szczytowych (Peak Hold)")
        self.show_peaks_cb.setChecked(self.config_mgr.get("audio_show_peaks", True))
        self.show_peaks_cb.toggled.connect(lambda v: self.update_cfg("audio_show_peaks", v))
        b_layout.addWidget(self.show_peaks_cb)

        layout.addWidget(box)
        layout.addStretch()

    def on_style_changed(self):
        val = self.style_combo.currentData()
        self.config_mgr.set("audio_style", val)
        self.settings_changed.emit()

    def on_sens_changed(self, val: int):
        sens = val / 10.0
        self.sens_lbl.setText(f"{sens:.1f}x")
        self.config_mgr.set("audio_sensitivity", sens)
        self.settings_changed.emit()

    def update_cfg(self, key: str, val: bool):
        self.config_mgr.set(key, val)
        self.settings_changed.emit()
