from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, QComboBox,
    QGroupBox, QPushButton, QFileDialog, QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from lcd_core.config_manager import ConfigManager

class CustomTab(QWidget):
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

        # Background Configuration Group
        bg_group = QGroupBox("🎨 Tło panelu hybrydowego")
        bg_layout = QVBoxLayout(bg_group)

        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Typ tła:"))
        self.bg_type_combo = QComboBox()
        bg_items = [
            ("Cyberpunk Dark Gradient", "gradient"),
            ("Własne zdjęcie / Grafika w tle", "image"),
            ("Jednolicie czarne (OLED)", "solid")
        ]
        for text, data in bg_items:
            self.bg_type_combo.addItem(text, data)
        curr_bg = self.config_mgr.get("custom_background_type", "gradient")
        idx = ["gradient", "image", "solid"].index(curr_bg) if curr_bg in ["gradient", "image", "solid"] else 0
        self.bg_type_combo.setCurrentIndex(idx)
        self.bg_type_combo.currentIndexChanged.connect(self.on_bg_type_changed)
        type_layout.addWidget(self.bg_type_combo)
        bg_layout.addLayout(type_layout)

        # Image picker for background
        self.img_row = QHBoxLayout()
        self.bg_path_edit = QLineEdit()
        self.bg_path_edit.setPlaceholderText("Wybierz grafikę w tle...")
        self.bg_path_edit.setText(self.config_mgr.get("custom_bg_image", ""))
        self.bg_path_edit.textChanged.connect(lambda t: self.save_opt("custom_bg_image", t.strip()))
        self.img_row.addWidget(self.bg_path_edit)

        browse_bg_btn = QPushButton("Przeglądaj...")
        browse_bg_btn.clicked.connect(self.browse_bg_image)
        self.img_row.addWidget(browse_bg_btn)
        bg_layout.addLayout(self.img_row)

        layout.addWidget(bg_group)

        # Widget Modules Selector Group
        mod_group = QGroupBox("🧩 Moduły i elementy na ekranie (Zaznacz co chcesz widzieć)")
        mod_layout = QVBoxLayout(mod_group)

        # 1. Clock
        self.chk_clock = QCheckBox("🕒 Kompaktowy zegar i data (Nagłówek)")
        self.chk_clock.setChecked(self.config_mgr.get("custom_show_clock", True))
        self.chk_clock.toggled.connect(lambda c: self.save_opt("custom_show_clock", c))
        mod_layout.addWidget(self.chk_clock)

        # 2. CPU Bar
        self.chk_cpu = QCheckBox("⚡ Pasek zużycia CPU (%)")
        self.chk_cpu.setChecked(self.config_mgr.get("custom_show_cpu_bar", True))
        self.chk_cpu.toggled.connect(lambda c: self.save_opt("custom_show_cpu_bar", c))
        mod_layout.addWidget(self.chk_cpu)

        # 3. RAM Bar
        self.chk_ram = QCheckBox("💾 Pasek zużycia RAM (%)")
        self.chk_ram.setChecked(self.config_mgr.get("custom_show_ram_bar", True))
        self.chk_ram.toggled.connect(lambda c: self.save_opt("custom_show_ram_bar", c))
        mod_layout.addWidget(self.chk_ram)

        # 4. GPU Bar
        self.chk_gpu = QCheckBox("🎮 Pasek zużycia GPU (%)")
        self.chk_gpu.setChecked(self.config_mgr.get("custom_show_gpu_bar", True))
        self.chk_gpu.toggled.connect(lambda c: self.save_opt("custom_show_gpu_bar", c))
        mod_layout.addWidget(self.chk_gpu)

        # 5. Temps Badges
        self.chk_temps = QCheckBox("🌡️ Kafelki temperatur (CPU, GPU, NVMe SSD)")
        self.chk_temps.setChecked(self.config_mgr.get("custom_show_temps", True))
        self.chk_temps.toggled.connect(lambda c: self.save_opt("custom_show_temps", c))
        mod_layout.addWidget(self.chk_temps)

        layout.addWidget(mod_group)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def browse_bg_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz grafikę w tle", "", "Obrazy (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.bg_path_edit.setText(path)

    def on_bg_type_changed(self, idx: int):
        val = ["gradient", "image", "solid"][idx]
        self.config_mgr.set("custom_background_type", val)
        self.config_changed.emit()

    def save_opt(self, key: str, val):
        self.config_mgr.set(key, val)
        self.config_changed.emit()
