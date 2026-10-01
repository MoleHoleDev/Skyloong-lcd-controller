import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QSlider, QGroupBox, QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from lcd_core.config_manager import ConfigManager

class GifTab(QWidget):
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

        # File Selection Group
        file_group = QGroupBox("🎞️ Wybór animacji GIF")
        file_layout = QVBoxLayout(file_group)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Wybierz plik animacji (*.gif)...")
        self.path_edit.setText(self.config_mgr.get("gif_path", ""))
        self.path_edit.textChanged.connect(self.on_path_changed)
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("Przeglądaj GIF...")
        browse_btn.setObjectName("AccentButton")
        browse_btn.clicked.connect(self.browse_file)
        path_layout.addWidget(browse_btn)
        file_layout.addLayout(path_layout)
        layout.addWidget(file_group)

        # Playback Settings Group
        settings_group = QGroupBox("⚡ Prędkość i odtwarzanie animacji")
        settings_layout = QVBoxLayout(settings_group)

        # Speed Slider (0.25x - 3.0x)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Prędkość odtwarzania:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(25, 300)
        curr_speed = int(self.config_mgr.get("gif_speed", 1.0) * 100)
        self.speed_slider.setValue(curr_speed)
        self.speed_lbl = QLabel(f"{curr_speed / 100.0:.2f}x")
        self.speed_slider.valueChanged.connect(self.on_speed_changed)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_lbl)
        settings_layout.addLayout(speed_layout)

        # Preset speed buttons
        presets_layout = QHBoxLayout()
        for label, val in [("0.5x", 50), ("1.0x (Normalna)", 100), ("1.5x", 150), ("2.0x (Szybka)", 200)]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, v=val: self.speed_slider.setValue(v))
            presets_layout.addWidget(btn)
        settings_layout.addLayout(presets_layout)

        layout.addWidget(settings_group)
        layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def browse_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz animację GIF", "", "Animowane GIFy (*.gif)"
        )
        if path:
            self.path_edit.setText(path)

    def on_path_changed(self, text: str):
        self.config_mgr.set("gif_path", text.strip())
        self.config_changed.emit()

    def on_speed_changed(self, val: int):
        speed_val = val / 100.0
        self.speed_lbl.setText(f"{speed_val:.2f}x")
        self.config_mgr.set("gif_speed", speed_val)
        self.config_changed.emit()
