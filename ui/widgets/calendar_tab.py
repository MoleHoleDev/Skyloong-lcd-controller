from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QGroupBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from lcd_core.config_manager import ConfigManager

class CalendarTab(QWidget):
    config_changed = Signal()

    def __init__(self, config_mgr: ConfigManager, parent=None):
        super().__init__(parent)
        self.config_mgr = config_mgr
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        theme_group = QGroupBox("📅 Motyw i stylistyka kalendarza")
        theme_layout = QVBoxLayout(theme_group)

        combo_layout = QHBoxLayout()
        combo_layout.addWidget(QLabel("Motyw kolorystyczny:"))
        self.theme_combo = QComboBox()
        theme_items = [
            ("Ciemny Cyber / Neon Blue", "neon_cyan"),
            ("Matrix Purple Glow", "purple_matrix"),
            ("Amoled Gold & Slate", "amoled_gold"),
            ("Minimalistyczny Mono", "minimal_mono")
        ]
        for text, data in theme_items:
            self.theme_combo.addItem(text, data)
        curr_theme = self.config_mgr.get("calendar_theme", "neon_cyan")
        self.theme_combo.setCurrentIndex(0)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        combo_layout.addWidget(self.theme_combo)
        theme_layout.addLayout(combo_layout)

        self.clock_check = QCheckBox("Pokazuj aktualną godzinę w nagłówku kalendarza")
        self.clock_check.setChecked(self.config_mgr.get("calendar_show_clock", True))
        self.clock_check.toggled.connect(self.on_clock_toggled)
        theme_layout.addWidget(self.clock_check)

        layout.addWidget(theme_group)

        # Info Box
        info_group = QGroupBox("ℹ️ Opcje widoku")
        info_layout = QVBoxLayout(info_group)
        info_lbl = QLabel(
            "Kalendarz automatycznie wyróżnia dzisiejszy dzień,\n"
            "wyświetla numer tygodnia ISO oraz dni wolne od pracy (So, Nd)."
        )
        info_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; line-height: 1.4;")
        info_layout.addWidget(info_lbl)
        layout.addWidget(info_group)

        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def on_theme_changed(self, idx: int):
        themes = ["neon_cyan", "purple_matrix", "amoled_gold", "minimal_mono"]
        self.config_mgr.set("calendar_theme", themes[idx])
        self.config_changed.emit()

    def on_clock_toggled(self, checked: bool):
        self.config_mgr.set("calendar_show_clock", checked)
        self.config_changed.emit()
