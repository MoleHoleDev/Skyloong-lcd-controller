import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
    QLineEdit, QComboBox, QGroupBox
)
from PySide6.QtCore import Signal
from lcd_core.config_manager import ConfigManager

class ScifiTerminalPanel(QWidget):
    settings_changed = Signal()

    def __init__(self, config_mgr: ConfigManager):
        super().__init__()
        self.config_mgr = config_mgr
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        box = QGroupBox("🚀 Ustawienia Sci-Fi Starship & Terminal HUD")
        b_layout = QVBoxLayout(box)

        # Ship Name
        n_row = QHBoxLayout()
        n_row.addWidget(QLabel("🛸 Nazwa statku / jednostki:"))
        self.ship_input = QLineEdit()
        self.ship_input.setText(self.config_mgr.get("scifi_ship_name", "GK104-PRO ORBITAL"))
        self.ship_input.textChanged.connect(self.on_ship_name_changed)
        n_row.addWidget(self.ship_input, 1)
        b_layout.addLayout(n_row)

        # Toggles
        self.show_radar_cb = QCheckBox("Wyświetlaj animowany radar taktyczny (Sweep)")
        self.show_radar_cb.setChecked(self.config_mgr.get("scifi_show_radar", True))
        self.show_radar_cb.toggled.connect(lambda v: self.update_cfg("scifi_show_radar", v))
        b_layout.addWidget(self.show_radar_cb)

        self.show_diag_cb = QCheckBox("Wyświetlaj pasek diagnostyki systemowej (DMA/Temperatury)")
        self.show_diag_cb.setChecked(self.config_mgr.get("scifi_show_diagnostics", True))
        self.show_diag_cb.toggled.connect(lambda v: self.update_cfg("scifi_show_diagnostics", v))
        b_layout.addWidget(self.show_diag_cb)

        layout.addWidget(box)
        layout.addStretch()

    def on_ship_name_changed(self, text: str):
        self.config_mgr.set("scifi_ship_name", text)
        self.settings_changed.emit()

    def update_cfg(self, key: str, val: bool):
        self.config_mgr.set(key, val)
        self.settings_changed.emit()
