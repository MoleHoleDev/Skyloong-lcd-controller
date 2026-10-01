from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, QButtonGroup,
    QCheckBox, QComboBox, QGroupBox, QPushButton, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from lcd_core.config_manager import ConfigManager

class ClockTab(QWidget):
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

        # Clock Style Selection Group
        style_group = QGroupBox("🕒 Styl i wygląd zegara")
        style_layout = QVBoxLayout(style_group)

        self.btn_group = QButtonGroup(self)
        styles = [
            ("🚀 Cyberpunk Neon (Pasek sekund, data, styl sci-fi)", "cyberpunk"),
            ("⏱️ Cyfrowy Modern (Duże czytelne cyfry)", "digital_modern"),
            ("📟 Retro Zielony LCD (Klasyczny monochromatyczny)", "retro_lcd"),
            ("🔲 Minimalistyczny (Czysty kontrast)", "minimal"),
            ("🕒 Klasyczny Analogowy (Wskazówkowy)", "analog")
        ]

        current_style = self.config_mgr.get("clock_style", "cyberpunk")
        for idx, (label, val) in enumerate(styles):
            rb = QRadioButton(label)
            rb.setProperty("style_val", val)
            if val == current_style:
                rb.setChecked(True)
            self.btn_group.addButton(rb, idx)
            style_layout.addWidget(rb)

        self.btn_group.buttonToggled.connect(self.on_style_toggled)
        layout.addWidget(style_group)

        # Color & Format Options Group
        options_group = QGroupBox("🎨 Akcenty kolorystyczne i format")
        options_layout = QVBoxLayout(options_group)

        # Accent Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Kolor akcentu / podświetlenia:"))
        self.color_combo = QComboBox()
        colors = [
            ("Cyjan / Neon Blue (#00f0ff)", "#00f0ff"),
            ("Magenta / Cyber Pink (#d946ef)", "#d946ef"),
            ("Szmaragdowy / Matrix Green (#10b981)", "#10b981"),
            ("Złoty / Amber Gold (#f59e0b)", "#f59e0b"),
            ("Czysta Biel (#ffffff)", "#ffffff"),
            ("Czerwień / Crimson (#ef4444)", "#ef4444")
        ]
        curr_color = self.config_mgr.get("clock_accent_color", "#00f0ff")
        for i, (name, hex_val) in enumerate(colors):
            self.color_combo.addItem(name, hex_val)
            if hex_val.lower() == curr_color.lower():
                self.color_combo.setCurrentIndex(i)

        self.color_combo.currentIndexChanged.connect(self.on_color_changed)
        color_layout.addWidget(self.color_combo)
        options_layout.addLayout(color_layout)

        # Format switches
        self.sec_check = QCheckBox("Pokazuj sekundy")
        self.sec_check.setChecked(self.config_mgr.get("clock_show_seconds", True))
        self.sec_check.toggled.connect(lambda c: self.save_opt("clock_show_seconds", c))
        options_layout.addWidget(self.sec_check)

        self.date_check = QCheckBox("Pokazuj datę i dzień tygodnia")
        self.date_check.setChecked(self.config_mgr.get("clock_show_date", True))
        self.date_check.toggled.connect(lambda c: self.save_opt("clock_show_date", c))
        options_layout.addWidget(self.date_check)

        layout.addWidget(options_group)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def on_style_toggled(self, button, checked):
        if checked:
            val = button.property("style_val")
            self.config_mgr.set("clock_style", val)
            self.config_changed.emit()

    def on_color_changed(self, idx: int):
        val = self.color_combo.currentData()
        self.config_mgr.set("clock_accent_color", val)
        self.config_changed.emit()

    def save_opt(self, key: str, val: bool):
        self.config_mgr.set(key, val)
        self.config_changed.emit()
